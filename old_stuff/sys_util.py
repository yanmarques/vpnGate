def run_shell(command):
    from subprocess import run, PIPE
    return run(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)