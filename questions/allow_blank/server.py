import random
import string
import math

#parses data["correct_answers"] and data["submitted_answers"] to a list format
def string_to_list(value: str):
    if value is None:
        return None
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    value = value.split(",")
    value = [v.strip() for v in value]
    return value

def generate(data):
    pass

def grade(data):

    pass
    # # score table B
    # # note: the values in the tables are only integers and strings, so we can perform a direct comparison (after lowercase).
    # # for more complex data types like a binary/hexadecimal value, you can reference how the grade function in pl-array-input
    # # uses the check_answer function.
    # B_score = 0

    # # get the correct answers for table B, which should be filled
    # correct_answer_B = data["correct_answers"]["q2"]
    # correct_answer_B = string_to_list(correct_answer_B)

    # num_rows = len(correct_answer_B)
    # for key in range(num_rows):
    #     sub = data["submitted_answers"]["q2_" + str(key)].lower()
    #     if sub == correct_answer_B[key]:
    #         data["partial_scores"]["q2_" +  str(key)] = {"score" : 1, "weight" : 0, "feedback" : "Correct."}
    #         B_score += 1
    #     else:
    #         data["partial_scores"]["q2_" +  str(key)] = {"score" : 0, "weight" : 0, "feedback" : "Incorrect."}
    

    # # if everything in table C is accurate, we want to give more weight to table B.
    # # Otherwise, we want to give an equal weight to both questions.
    # if (data["submitted_answers"]["q3_" + str(key)].lower() == "" for key in range(num_rows)):
    #     print("all values in q3 are blank")
    #     data["partial_scores"]["q2"] = {"score": B_score / num_rows, "weight": 2}
    #     data["partial_scores"]["q3"] = {"score": 1, "weight": 1}
    # else:
    #     print("values in q3 are not blank")
    #     # score table C
    #     C_score = 0
    #     for key in range(num_rows):
    #         sub = data["submitted_answers"]["q3_" + str(key)].lower()
    #         if sub == "":
    #             data["partial_scores"]["q3_" +  str(key)] = {"score" : 1, "weight" : 0, "feedback" : "Correct."}
    #             C_score += 1
    #         else:
    #             data["partial_scores"]["q3_" +  str(key)] = {"score" : 0, "weight" : 0, "feedback" : "Incorrect."}
    #     data["partial_scores"]["q2"] = {"score": B_score / num_rows, "weight": 1}
    #     data["partial_scores"]["q3"] = {"score": C_score / num_rows, "weight": 1}
    # return