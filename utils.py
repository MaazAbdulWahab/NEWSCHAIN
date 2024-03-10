import random
import string


def generate_random_string(length):
    # Define the characters you want to include in the random string
    characters = string.ascii_letters

    # Generate the random string
    random_string = "".join(random.choice(characters) for i in range(length))

    return random_string
