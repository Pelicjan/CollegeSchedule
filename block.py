class Block:

    def __init__(self, **kwargs):
        self.index = kwargs.get('index', -1)
        self.blank = kwargs.get('blank', True)
        self.group = kwargs.get('group', '')
        self.hide = kwargs.get('hide', False)
        self.note = kwargs.get('note', '')
        self.subject = kwargs.get('subject', '')
        self.category = kwargs.get('category', '')
        self.room = kwargs.get('room', '')
        self.teacher = kwargs.get('teacher', '')
        self.number = kwargs.get('number', '')
