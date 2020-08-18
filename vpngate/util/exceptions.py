class InvalidProofOfWork(Exception):
    def __init__(self, proof: int):
        message = f'The provided Proof-of-Work value is not valid: {proof}'
        super().__init__(message)
        self.proof = proof
