def get_position(init_position):
    current = init_position
    def f(length):
        nonlocal current
        current -= length
        return current

    return f

x = get_position(150)
print(x(12))
print(x(12))

