# Misc handy utils

def hassuffix(st, suff):
    """Return whether string (usually file name) has given suffix"""
    try:
        if st[st.rindex(suff):] == suff: return True
    except ValueError:
        pass
    return False

