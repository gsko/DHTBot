"""
Utilities that make using pickle without files very easy

"""
import StringIO
import pickle


def pickle_to_str(obj):
    """
    Pickle an object directly to a string
    """
    # Simulate file IO with the StringIO object
    output_file = StringIO.StringIO()
    pickle.dump(obj, output_file)
    return output_file.getvalue()

def unpickle_from_str(obj_str):
    """
    Unpickle an object directly from a string
    """
    # Simulate file IO with the StringIO object
    input_file = StringIO.StringIO(obj_str)
    obj = pickle.load(input_file)
    return obj
