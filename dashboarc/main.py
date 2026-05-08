from constants import *
from controller import *
from integration import *
from model import *
from view import *
from graph import *

eventQueue = queue.Queue()

# ===============================================================
# main():
def main():
    port = sys.argv[1] if len(sys.argv) == 2 else None

    view = View()
    model = Model()
    integration = Integration()
    controller = Controller(view, model, integration, eventQueue, port)

    view.build()
    eventDispatcher(view.root)
    #drawGraphs(view.root)
    view.root.mainloop()
    return 0

# ===============================================================
# eventDispatcher():
#   Checks for new events every 10 ms.
#   This is a wrapper function that retreives the callbacks from
#   any observer.notify() because only main thread can update UI
#   | NewModel | -> Observer.notify() -> eventQueue.put(ui.update())
def eventDispatcher(root: ctk.CTk):
    try:
        observer, subject = eventQueue.get_nowait()
        observer(subject)
    except queue.Empty:
        pass

    root.after(10, eventDispatcher, root)

#def drawGraphs(root: ctk.CTk):
    #plt.pause(1)
    #root.after(1000, drawGraphs, root)

def initController(view, model, integration, eventQueue, port):
    return Controller(view, model, integration, eventQueue, port)

if __name__ == "__main__":
    main()