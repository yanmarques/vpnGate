class InvalidProofOfWork(Exception):
    def __init__(self, proof: int):
        super().__init__(f'The provided Proof-of-Work value is not valid: {proof}')
        self.proof = proof