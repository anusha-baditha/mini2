import random
def genotp():
    u_l=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    s_l=[chr(i) for i in range(ord('a'),ord('z')+1)]
    otp=''
    for i  in range(1):  #the otp size is 4
        otp+=str(random.randint(0,9))   #otp='9'
        otp=otp+random.choice(u_l)      #otp='9S'
        otp=otp+random.choice(s_l)      #otp='9Sf'
        otp+=str(random.randint(0,9))   #otp='9Sf5'
    return otp

