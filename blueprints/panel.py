import sqlite3

from flask import Blueprint, render_template, current_app, redirect, request, flash
from .models import Request, VoteRequest


web = Blueprint('control', __name__, template_folder='templates')


@web.route('/')
def index():
    builder = Request.with_votes_count().order_by('created_at')
    accepteds = False

    if 'accepted' in request.args:
        accepteds = request.args['accepted'].lower() == 'true'
        builder = Request.q_accepted(query=builder, status=accepteds)
    all_requests = builder.get()
    return render_template('listing.html.j2', 
                        requests=all_requests,
                        is_accepteds=accepteds,
                        min_votes=Request.min_votes())


@web.route('/accept/<req_id>', methods=['post'])
def accept_request(req_id):
    current_app.logger.debug('recv accept to: %s', req_id)
    vote_req = VoteRequest(request_id=req_id, ip_address=request.remote_addr)
    
    state = vote_req.create()
    if state is True:
        votes_count = VoteRequest.count_by_request(req_id=req_id).return_raw().first(columns=[])[0]
        current_app.logger.debug('request votes count: %s', votes_count)
        if votes_count >= Request.min_votes():
            current_app.logger.debug('request has been accepted: %s', req_id)
            Request(id=req_id, accepted=True).update()
    elif type(state) is list:
        current_app.logger.debug('vote request errors: %s', state)
        if 'request_id_fk' in state:
            flash('Unknow request id.')
        else:
            flash('You must not vote for this request again!')
    else:
        flash('Unexpected error happened. Please contact any administrator.')

    return redirect('/')
