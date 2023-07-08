# Actors extend the Ray API from functions (tasks) to classes. An actor
# is essentially a stateful worker (or a service). When a new actor is instantiated,
# a new worker is created, and methods of the actor are scheduled on that specific
# worker and can access and mutate the state of that worker. Like tasks, actors
# support CPU, GPU, and custom resource requirements.

# Remote Classes (just as remote tasks) use a @ray.remote decorator on a Python class.

# Ray Actor pattern is powerful. They allow you to take a Python class and instantiate
# it as a stateful microservice that can be queried from other actors and tasks and
# even other Python applications. Actors can be passed as arguments to other tasks
# and actors.

# When you instantiate a remote Actor, a separate worker process is attached to a worker
# process and becomes an Actor process on that worker node—all for the purpose of running
# methods called on the actor. Other Ray tasks and actors can invoke its methods on that
# process, mutating its internal state if desried. Actors can also be terminated manually
# if needed. The examples code below show all these cases.

# So let's look at some examples of Python classes converted into Ray Actors.

import logging
import time
import ray
import random
from random import randint
import numpy as np

if ray.is_initialized:
    ray.shutdown()
ray.init(logging_level=logging.ERROR)
# ray.init(address='auto', ignore_reinit_error=True, logging_level=logging.ERROR)

# Remote class as a stateful actor pattern
#
# Example 1: Method tracking
#
# Problem: We want to keep track of who invoked a particular method. This
# could be a use case for telemetry data we want to track.

# Let's use this actor to track method invocation of an actor methods. Each
# instance will track who invoked it and number of times.

CALLERS=["A","B","C"]

@ray.remote
class MethodStateCounter :
    def __init__(self) :
        self.invokers={"A" : 0,"B" : 0,"C" : 0}
        self.invokers_counted_values={"A" : [],"B" : [],"C" : []}

    def invoke(self,name) :
        # pretend to do some work here
        time.sleep(0.5)
        # update times invoked
        self.invokers[name]+=1
        # return the state of that invoker
        rand_num = random.randint(5,25)
        self.invokers_counted_values[name].append(rand_num)
        return rand_num

    def get_invoker_state(self,name) :
        # return the state of the named invoker
        return self.invokers[name]

    def get_all_invoker_state(self) :
        # reeturn the state of all invokers
        return self.invokers

    def get_invoker_computed_values(self, names_arr):
        return [(name, self.invokers_counted_values[name]) for name in names_arr]


# Create an instance of our Actor
# worker_invoker = MethodStateCounter.remote()
# print(worker_invoker)

# Iterate and call the invoke() method by random callers and keep track of who
# called it.

# for _ in range(10):
#     name = random.choice(CALLERS)
#     worker_invoker.invoke.remote(name)

# Invoke a random caller and fetch the value or invocations of a random caller

# print('method callers')
# for _ in range(5):
#     random_name_invoker = random.choice(CALLERS)
#     times_invoked = ray.get(worker_invoker.invoke.remote(random_name_invoker))
#     print(f"Named caller: {random_name_invoker} called {times_invoked}")

# Fetch the count of all callers
# print(ray.get(worker_invoker.get_all_invoker_state.remote()))


# excercise 3

# 3.0 start remote cluster settings and observe actors in cluster
# a) make screenshot of dependencies
# 3.1. Modify the Actor class MethodStateCounter and add/modify methods that return the following:
worker_invoker = MethodStateCounter.remote()
print(worker_invoker)
for _ in range(10):
    name = random.choice(CALLERS)
    worker_invoker.invoke.remote(name)


# a) - Get number of times an invoker name was called
for _ in range(3):
    random_name_invoker = random.choice(CALLERS)
    times_invoked = ray.get(worker_invoker.get_invoker_state.remote(random_name_invoker))
    print(f"Named caller: {random_name_invoker} called {times_invoked}")

# b) - Get a list of values computed by invoker name
names_arr = ["A", "C"]
print(f"Values computed by invokers {ray.get(worker_invoker.get_invoker_computed_values.remote(names_arr))}")

# 3- Get state of all invokers
# print(ray.get(worker_invoker.get_all_invoker_state.remote()))
# 3.2 Modify method invoke to return a random int value between [5, 25]

# 3.3 Take a look on implement parralel Pi computation
# based on https://docs.ray.io/en/master/ray-core/examples/highly_parallel.html
#
# Implement calculating pi as a combination of actor (which keeps the
# state of the progress of calculating pi as it approaches its final value)
# and a task (which computes candidates for pi)


# Note that we did not have to reason about where and how the actors are scheduled.
# We did not worry about the socket connection or IP addresses where these actors
# reside. All that's abstracted away from us.
# All we did is write Python code, using Ray core APIs, convert our classes into
# distributed stateful services

# Example 2: Parameter Server distributed application with Ray Actors
# Problem: We want to update weights and gradients, computed by workers,
# at a central server.
# Let's use Python class and convert that to a remote Actor class
# actor as a Parameter Server.
# This is a common example in machine learning where you have a central
# Parameter server updating gradients from other worker processes computing
# individual gradients.

# print('parameter server')
@ray.remote
class ParameterSever:
    def __init__(self):
        # Initialized our gradients to zero
        self.params = np.zeros(10)

    def get_params(self):
        # Return current gradients
        return self.params

    def update_params(self, grad):
        # Update the gradients
        self.params -= grad

# Define a worker or task as a function for a remote Worker. This could be a
# machine learning function that computes gradients and sends them to
# the parameter server.

@ray.remote
def worker(ps):         # It takes an actor handle or instance as an argument
    # Iterate over some epoch
    for i in range(25):
        time.sleep(1.5)  # this could be your loss function computing gradients
        grad = np.ones(10)
        # update the gradients in the parameter server
        ps.update_params.remote(grad)

# Start our Parameter Server actor. This will be scheduled as a worker process
# on a remote Ray node. You invoke its ActorClass.remote(...) to instantiate an
# Actor instance of that type.

# param_server = ParameterSever.remote()
# print(param_server)

# Let's get the initial values of the parameter server
# print(f"Initial params: {ray.get(param_server.get_params.remote())}")

# Create Workers remote tasks computing gradients
# Let's create three separate worker tasks as our machine learning tasks
# that compute gradients. These will be scheduled as tasks on a Ray cluster.

# You can use list comprehension.
# If we need more workers to scale, we can always bump them up.
# Note: We are sending the parameter_server as an argument to the remote worker task.

# print([worker.remote(param_server) for _ in range(3)])

# Now, let's iterate over a loop and query the Parameter Server as the
# workers are running independently and updating the gradients

# for _i in range(20):
#     print(f"Updated params: {ray.get(param_server.get_params.remote())}")
#     time.sleep(1)

# Tree of Actors Pattern
# A common pattern used in Ray libraries Ray Tune, Ray Train, and RLlib
# to train models in a parallel or conduct distributed HPO.

# In this common pattern, tree of actors, a collection of workers as actors, are
# managed by a supervisor actor. For example, you want to train multiple models,
# each of a different type, at the same time, while being able to inspect its
# state during its training.

# Example: Supervisor and worker actor pattern
# Generic model factory utility
# This factory generates a few specify type of models (they are fake):
# regression, classification, or neural network, and will have its respective
# training function. Each model will be in a particular state during training.
# The final state is DONE.

# Factory function to return an instance of a model type
def model_factory(m: str, func: object):
    return Model(m, func)

# states to inspect or checkpoint
STATES = ["RUNNING", "PENDING", "DONE"]

class Model:

    def __init__(self, m:str, func: object):
        self._model = m
        self._func = func

    def train(self):
        # do some training work here for the respective model type
        self._func()

#This worker actor will train each model. When the model's state reaches DONE, we stop training

@ray.remote
class Worker(object) :
    def __init__(self,m: str,func: object) :
        # type of a model: lr, cl, or nn
        self._model=m
        self._func=func

    # inspect its current state and return it. For now
    # it could be in one of the states
    def state(self) -> str :
        return random.choice(STATES)

    # Create the model from the factory for this worker and
    # do the training by invoking its respective objective function
    # for that model
    def work(self) -> None :
        model_factory(self._model,self._func).train( )

#The supervisor creates three actors, each with its own respective training model
# type and its training function.

# Define respective model training functions

def lf_func() :
    # do some training work for linear regression
    time.sleep(1)
    return 0


def cl_func() :
    # do some training work for classification
    time.sleep(1)
    return 0


def nn_func() :
    # do some training work for neural networks
    time.sleep(1)
    return 0


@ray.remote
class Supervisor :
    def __init__(self) :
        # Create three Actor Workers, each by its unique model type and
        # their respective training function
        self.workers=[Worker.remote(name,func) for (name,func)
                      in [("lr",lf_func),("cl",cl_func),("nn",nn_func)]]

    def work(self) :
        # do the work
        [worker.work.remote( ) for worker in self.workers]

    def terminate(self) :
        [ray.kill(worker) for worker in self.workers]

    def state(self) :
        return ray.get([worker.state.remote( ) for worker in self.workers])

# Create a Actor instance for supervisor and launch its workers

# sup = Supervisor.remote()

# Launch remote actors as workers
# print(sup.work.remote())

# Look at the Ray Dashboard. You should see Actors running as process on the
# workders nodes Supervisor and Workers

# Also, click on the Logical View to view more metrics and data on individual Ray Actors

# check their status
# while True :
#     # Fetch the states of all its workers
#     states=ray.get(sup.state.remote( ))
#     print(states)
#     # check if all are DONE
#     result=all('DONE'==e for e in states)
#     if result :
#         # Note: Actor processes will be terminated automatically when the initial actor handle goes out of scope in Python.
#         # If we create an actor with actor_handle = ActorClass.remote(), then when actor_handle goes out of scope and is destroyed,
#         # the actor process will be terminated. Note that this only applies to the original actor handle created for the actor
#         # and not to subsequent actor handles created by passing the actor handle to other tasks.
#
#         # kill supervisors' all workers manually, only for illustrtation and demo
#         sup.terminate.remote( )
#
#         # kill the supervisor manually, only for illustration and demo
#         ray.kill(sup)
#         break



# excercise 3.3 Take a look on implement parralel Pi computation
# based on https://docs.ray.io/en/master/ray-core/examples/highly_parallel.html
#
# Implement calculating pi as a combination of actor (which keeps the
# state of the progress of calculating pi as it approaches its final value)
# and a task (which computes candidates for pi)

#Rozwiązanie w oparciu o https://docs.ray.io/en/master/ray-core/examples/monte_carlo_pi.html
@ray.remote
class PiActor:
    def __init__(self, total_points):
        self.total_points = total_points
        self.points_per_task = {}

    def save_progress(self, task_id, points_counted):
        self.points_per_task[task_id] = points_counted

    def get_progress(self):
        return sum(self.points_per_task.values()) / total_points


@ray.remote
def estimate_pi(num_points, task_id, actor):
    num_inside = 0
    for i in range(num_points):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        distance = x ** 2 + y ** 2
        if distance <= 1:
            num_inside += 1

        if (i + 1) % 1000000 == 0:
            actor.save_progress.remote(task_id, i + 1)

    actor.save_progress.remote(task_id, num_points)
    return num_inside



tasks = 10
points_per_task = 10_000_000
total_points = tasks * points_per_task

actor = PiActor.remote(total_points)

results = [
    estimate_pi.remote(points_per_task, i, actor)
    for i in range(tasks)
]

while True:
    progress = ray.get(actor.get_progress.remote())
    print(f"Progress: {int(progress * 100)}%")

    if progress == 1:
        break

    time.sleep(1)

total_num_inside = sum(ray.get(results))
pi = (total_num_inside * 4) / total_points
print(f"Estimated value of π is: {pi}")

ray.shutdown()