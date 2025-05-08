class TimelineItem:
    def __init__(self, type, title, when, is_future, reference_id):
        self.type = type
        self.title = title
        self.when = when
        self.is_future = is_future
        self.reference_id = reference_id
