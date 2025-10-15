# this pyfile is using to generate unique string like : password or filename
# it will generate a random string based on the current timestamp and a random string
# the length of the random string can be set by the k parameter, default is 8
# the suffix can be set by the suffix parameter, default is ".txt"

import random
import string
from datetime import datetime
def shuffle_string(s):
    # 将字符串转换为列表
    char_list = list(s)
    # 使用 random.shuffle 打乱列表中的元素
    random.shuffle(char_list)
    # 将列表重新组合成字符串
    shuffled_string = ''.join(char_list)
    return shuffled_string

def unique_name(k=8):
    """
    Generate a unique string based on the current timestamp and a random string.

    Parameters
    ----------
    k : int, optional
        The length of the random string. Defaults to 8.
    suffix : str, optional
        The suffix to add to the end of the string. Defaults to ".txt".

    Returns
    -------
    str
        The generated unique string.
    """
    random_str = "".join(random.choices(string.ascii_letters + string.digits, k=k))
    filename = f"{int(datetime.now().timestamp())}_{shuffle_string(random_str)}"
    return filename

def unique_password(k=12):
    """
    Generate a unique password string based on the current timestamp and a random string.

    Parameters
    ----------
    k : int, optional
        The length of the random string. Defaults to 12.

    Returns
    -------
    str
        The generated unique password string.
    """
    chars_az = string.ascii_letters # 5
    chars_num = string.digits  # 5
    chars_punch = '#@$!'  # 2
    password = (''.join(random.choices(chars_az,k=5)) + 
                ''.join(random.choices(chars_num,k=5)) + 
                ''.join(random.choices(chars_punch,k=2)))
    
    password = shuffle_string(password)

    return password


if __name__ == "__main__":
    print(unique_name())
    print(unique_password())