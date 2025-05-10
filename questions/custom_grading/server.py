import random
import string
import math


#parses data["correct_answers"] and data["submitted_answers"]
def string_to_list(value: str):
    if value is None:
        return None
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    value = value.split(",")
    value = [v.strip() for v in value]
    return value

def grade(data):

    # get number of rows (based on output, not input)
    correct_answer = data["correct_answers"]["q1"]
    correct_answer = string_to_list(correct_answer)

    # want to prioritize changes to A[1], A[2], and A[3]
    priority_keys = [1, 2, 3]
    non_priority_incorrect = False
    priority_incorrect = False
    score_sum = 0
    num_rows = len(correct_answer)
    for key in range(num_rows):
        sub = data["submitted_answers"]["q1_" + str(key)]
        if sub == correct_answer[key]:
            data["partial_scores"]["q1_" +  str(key)] = {"score" : 1, "weight" : 0, "feedback" : "Correct."}
            score_sum += 1
        else:
            data["partial_scores"]["q1_" +  str(key)] = {"score" : 0, "weight" : 0, "feedback" : "Incorrect."}
            if key in priority_keys:
                priority_incorrect = True
            else:
                non_priority_incorrect = True
    
    # if priority keys are all correct, but non-priority keys are incorrect, grade normally
    # "normal" means that each input has the same weight
    if non_priority_incorrect:
        data["partial_scores"]["q1"] = {"score": score_sum / num_rows}
        return
    
    #else, prioritize the weights of the priority keys.
    score_sum = 0
    for key in priority_keys:
        score_sum += data["partial_scores"]["q1_" + str(key)]["score"]
    score_sum += 1 if not non_priority_incorrect else 0
    data["partial_scores"]["q1"] = {"score": score_sum / (len(priority_keys) + 1)}

    return