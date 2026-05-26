class LamportClock:
    def __init__(self, start: int = 0):
        self.value = int(start)

    def tick(self) -> int:
        self.value += 1
        return self.value

    def update(self, remote_value: int) -> int:
        self.value = max(self.value, int(remote_value)) + 1
        return self.value
