class Block:
    def __init__(self, block_start=1, block_end=28):
        assert -5 <= block_start <= 7, f"Block start is {block_start}, but must begin within 7 days of day 1"
        assert 22 <= block_end <= 34, f"Block end is {block_end}, but must end within 7 days of day 28"
        self.start = block_start
        self.end = block_end
        print(f'Creating {self}')

    def __repr__(self):
        return f'Block=[{self.start}, {self.end}]'
