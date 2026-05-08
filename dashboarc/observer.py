from constants import *


# =========================================================================	
# Observer:
#   self.observers is a list of functions 
#   notify() calls these functions with "self" = Subject class.
class Observer:
    def __init__(self):
        self.observers = []
        self.eventQueue = None

    def notify(self):
        for observer in self.observers:
            self.eventQueue.put((observer, self))
            #observer(self)

    def attach(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def detach(self, observer):
        try:
            self.observers.remove(observer)
        except ValueError:
            pass