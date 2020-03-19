import importlib
import os
from functools import partial
from multiprocessing import Process, Queue

from flask import Flask, request

app = Flask("serverfull")

workers = {}

def load_bees_module_names():
    exclude = set(["__pycache__"])
    bee_modules = filter(
        os.path.isdir, [
            os.path.join("./bees/", module) for module in os.listdir("./bees/")
        ]
    )
    bee_modules = set(map(os.path.basename, bee_modules))
    bee_modules = bee_modules.difference(exclude)
    return list(bee_modules)


bees = load_bees_module_names()


def bee_loop(handler, inq, outq):
    request = inq.get()
    print("Got request")
    outq.put(handler(request))


def generic_handler(bee_path):
    _, inq, outq = workers[bee_path]
    print(f"Putting {request.args}")
    inq.put(request.args)
    return outq.get()


for bee in bees:
    bee_path = f"bees.{bee}"
    print(f"Importing {bee_path}")
    bee_mod = importlib.import_module(bee_path)
    bee_mod = importlib.reload(bee_mod)  # TODO: be smarter, but who cares
    print(f"/bees/{bee} => {bee_mod.handler}")
    inq = Queue()
    outq = Queue()
    proc = Process(target=bee_loop, args=(bee_mod.handler, inq, outq))
    proc.start()
    workers[bee_path] = [proc, inq, outq]
    app.add_url_rule(f"/bees/{bee}", f"bee.{bee}", partial(generic_handler, (bee_path)))
