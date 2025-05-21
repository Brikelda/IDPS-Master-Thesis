def get_pending_command():
    return [
        {'FLOW.PUMP2': 900, 'FLOW.PUMP1': 300},
        {'FLOW.PUMP4': 800, 'STATE.PUMP4': 1},
        {'OUTPUTVALVE.CLOSE': 1}
    ]