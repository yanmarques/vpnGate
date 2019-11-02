import sqlite3

from flask import current_app


def get_conn():
    return current_app.get_db()


def join(fields):
    return ','.join(fields)


class QueryBuilder:
    def __init__(self, table, class_factory):
        self.class_factory = class_factory
        self.sql = ''
        self.table = table
        self.filters = []
        self.projections = []
        self.froms = []
        self.orders = []
        self.joins = []
        self.payload = []

    def where(self, field, value, operator='=', raw=False):
        self.filters.append([field, operator, value, raw])
        return self

    def project(self, expression, alias=None):
        if isinstance(expression, QueryBuilder):
            payload = expression._compile_select(columns=[])
            self.payload.extend(payload)
            expression = f'({expression.sql})'
        if alias:
            expression = expression.rstrip("\s") + f' as {alias}'
        self.projections.append(expression)
        return self

    def select(self, table):
        self.froms.append(table)
        return self

    def order_by(self, column):
        self.orders.append(column)
        return self

    def join(self, foreign_table, local_col, foreign_col, mode='inner'):
        self.joins.append([foreign_table, local_col, foreign_col, mode])
        return self

    def get(self, **kwargs):
        payload = self._compile_select(**kwargs)
        for item in self._execute(payload):
            yield self.class_factory(item)

    def return_raw(self):
        self.class_factory = lambda item: item
        return self

    def set(self, data: dict):
        fields = list(map(lambda k: f'{k} = ?', data.keys()))
        payload = list(data.values())
        self.sql = f'update {self.table} set {join(fields)}'
        payload.extend(self.__apply_filters())
        return self._execute(payload)

    def create(self, data: dict):
        fields = list(data)
        payload = list(data.values())
        mask = join(['?' for _ in payload])

        self.sql = f'insert into {self.table} ({join(fields)}) values ({mask})'
        return self._execute(payload).lastrowid
    
    def first(self, **kwargs):
        payload = self._compile_select(**kwargs)
        return self._execute(payload).fetchone()

    def _compile_select(self, columns=['*']):
        list(map(self.project, columns))
        self.__init_statement()
        payload = self.__apply_filters()
        self.__apply_orders()
        return payload

    def __apply_filters(self):
        if not len(self.filters):
            return []
        self.sql = self.sql.rstrip("\s") + ' where'
        payload = []
        for item in self.filters:
            expression = f' {item[0]} {item[1]} ' 
            if item[3]: # when it's a raw value
                expression += item[2]
            else:
                expression += '?'
                payload.append(item[2])
            self.sql += expression + ' and'
        self.sql = self.sql.rstrip('and')
        return payload
        
    def __init_statement(self):
        self.sql = 'select ' + join(self.projections).rstrip("\s")
        self.sql += ' from ' + join([self.table] + self.froms).rstrip("\s")
        for join_exp in self.joins:
            self.sql += f' {join_exp[3]} join {join_exp[0]} on {join_exp[1]} = {join_exp[2]} and' 
        self.sql = self.sql.rstrip('and')

    def __apply_orders(self):
        if len(self.orders):
            self.sql = self.sql.rstrip("\s") + ' order by ' + join(self.orders)

    def _execute(self, payload=[]):
        conn = get_conn()
        self.payload.extend(payload)
        current_app.logger.debug('executing SQL: %s', self.sql)
        current_app.logger.debug('SQL payload: %s', self.payload)
        return conn.execute(self.sql, self.payload)


class BaseModel(dict):
    attrs = []
    table = None
    synced = False
    auto_increment = True

    @property
    def query(self):
        return QueryBuilder(self.table, self._mount_object)    

    def create(self, sync=False):
        # safely pass data values to payload
        payload = self._get_data()
        assert len(payload), 'Invalid information to create model.'

        def create_and_sync():
            result_id = self._make_creation(payload)
            if sync:
                self.sync(identifier=result_id)
        return self._handle_query(create_and_sync)

    def update(self, identifier=None, only=None):
        assert len(self.values()), 'Invalid update information.'

        filter_action = lambda i: (only is None) or only and i[0] in only
        data = list(filter(filter_action, self._get_data()))
        assert len(data), 'Invalid update information, must no be empty.'

        def make_update():
            self.query.where('id', identifier or self['id']).set(data)
        return self._handle_query(make_update)

    def sync(self, identifier=None, force=False):
        if force or not self.synced:
            model = self.query.where('id', identifier or self['id']).first()
            current_app.logger.debug('model from database: %s', model)
            super().update(model)
            current_app.logger.debug('synced model: %s', self)

    def exists(self, identifier=None):
        return self.query.where('id', identifier or self['id']).return_raw().first(columns=['id']) is not None

    def _handle_query(self, callback):
        try:
            callback()
            get_conn().commit()
            return True
        except sqlite3.IntegrityError as exception:
            errors = self._get_error_bag(exception)
            if len(errors):
                return errors
            current_app.logger.error(str(exception))
        
    def _get_error_bag(self, exception):
        errors = []
        exc_text = str(exception).lower()
        for attr in self.attrs:
            if attr in exc_text:
                errors.append(attr)
        return errors

    def _make_creation(self, payload):
        if self.auto_increment:
            # retrieve last ID from db
            last_id = self.query.return_raw().first(columns=['max(id)'])[0] or 0
            payload['id'] = last_id + 1
        return self.query.create(payload)

    def _get_data(self):
        return dict([(k, v) for k,v in self.items() 
                if k in self.attrs])
    
    def _mount_object(self, item):
        return self.__class__(**item)


class Request(BaseModel):
    attrs = ['email', 'accepted', 'accepts_count']
    table = 'request'

    @staticmethod
    def with_votes_count():
        subquery = VoteRequest.count_by_request(as_subquery=True)
        return Request().query.project(subquery, alias='votes_count')

    @staticmethod
    def count_members():
        return Request.q_accepted().return_raw().first(columns=['count(*)'])[0]

    @staticmethod
    def min_votes():
        members_count = Request.count_members()
        current_app.logger.debug('number of active members: %s', members_count)
        return round(members_count / 2)

    @staticmethod
    def q_accepted(query=None, status=True):
        query = query or Request().query
        return query.where('accepted', status)


class VoteRequest(BaseModel):
    table = 'vote_request'
    attrs = ['ip_address', 'request_id']
    auto_increment = False

    def _make_creation(self, payload):
        request_id = self['request_id']
        request_exists = Request(id=request_id).exists()
        current_app.logger.debug(f'request id [{request_id}] exists: %s', request_exists)
        if not request_exists:
            raise sqlite3.IntegrityError('Colunm "request_id_fk" fails on foreign key constraint.')
        return super()._make_creation(payload)

    def _get_error_bag(self, exception):
        errors = super()._get_error_bag(exception)
        if 'request_id_fk' in str(exception): 
            errors.append('request_id_fk')
        return errors

    @staticmethod
    def count_by_request(req_id=None, as_subquery=False):
        if as_subquery:
            req_id = 'id'
        return VoteRequest().query.\
                project('count(*)').\
                    where('request_id', req_id, raw=as_subquery)