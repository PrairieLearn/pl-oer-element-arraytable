import random
import string
import math

def generate(data):
    # operations choices
    ops = ["*", "+"]

    # randomize array length
    array_len = random.randint(5, 10)
    answers = [i for i in range(array_len)]

    # use this for prefill and placeholder values in question.html
    data["params"]["prefill"] = [i for i in range(array_len)]

    # generate 3 random equations
    for i in range(1, 4):
        i1 = random.randint(0, array_len - 1)
        i2 = random.randint(0, array_len - 1)
        i3 = random.randint(0, array_len - 1)
        op = random.choice(ops)
        data["params"][f"eq{i}"] = f"A[{i1}] = A[{i2}] {op} A[{i3}];"
        if op == "*":
            answers[i1] = answers[i2] * answers[i3]
        elif op == "+":
            answers[i1] = answers[i2] + answers[i3]
    
    # can set correct answers in server.py instead of question.html
    data["correct_answers"]["q1"] = answers
