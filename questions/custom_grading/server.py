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

    # FIRST GRADING METHOD: 75 - 25

    # get number of rows (based on output, not input)
    correct_answer = data["correct_answers"]["q1"]
    correct_answer = string_to_list(correct_answer)

    # want to prioritize changes to A[1], A[2], and A[3]
    priority_keys = [1, 2, 3]
    non_priority_score = 0
    priority_score = 0
    num_rows = len(correct_answer)
    for key in range(num_rows):
        sub = data["submitted_answers"]["q1_" + str(key)]
        if sub == correct_answer[key]:
            data["partial_scores"]["q1_" +  str(key)] = {"score" : 1, "weight" : 0, "feedback" : "Correct."}
            score_sum += 1
            if (key in priority_keys):
                priority_score += 1
            else:
                non_priority_score += 1
        else:
            data["partial_scores"]["q1_" +  str(key)] = {"score" : 0, "weight" : 0, "feedback" : "Incorrect."}
    
    # ~~~~~~~~~~~give more weight to the the priority answers~~~~~~~~~~~~~~
    final_score = 0.75 * (priority_score/3) + 0.25 * (non_priority_score/8)

    data["partial_scores"]["q1"] = {"score": final_score}

    # SECOND GRADING METHOD: DETRACT FOR INNACURACIES OUTSIDE OF RELEVANT VALUES.


     # get number of rows (based on output, not input)
    correct_answer = data["correct_answers"]["q2"]
    correct_answer = string_to_list(correct_answer)

    # want to prioritize changes to A[1], A[2], and A[3]
    priority_keys = [1, 2, 3]
    non_priority_score = 0
    priority_score = 0
    num_rows = len(correct_answer)
    for key in range(num_rows):
        sub = data["submitted_answers"]["q1_" + str(key)]
        if sub == correct_answer[key]:
            data["partial_scores"]["q1_" +  str(key)] = {"score" : 1, "weight" : 0, "feedback" : "Correct."}
            score_sum += 1
            if (key in priority_keys):
                priority_score += 1
            else:
                non_priority_score += 1
        else:
            data["partial_scores"]["q1_" +  str(key)] = {"score" : 0, "weight" : 0, "feedback" : "Incorrect."}
    
   # ~~~~~~~~~~~subtract for non priority innacuracy~~~~~~~~~~~~~~
    final_score = max (0, (priority_score/3) - 0.25 * (non_priority_score/8))

    data["partial_scores"]["q1"] = {"score": final_score}

    return