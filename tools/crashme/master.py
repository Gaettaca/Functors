#!/usr/bin/python3
import os
import sys
import hmac
import datetime
import subprocess

if __name__ == "__main__":
    challanges = os.listdir("challenges")
    
    sys.stdout.write("Select challenge ({}):".format(",".join(challanges)))
    sys.stdout.flush()

    challenge = sys.stdin.readline(1024).strip()
    if challenge not in challanges:
        sys.stdout.write("Don't know '{}'\n".format(challenge))
        sys.exit(0)

    p = subprocess.run(["./challenges/" + challenge], stdin=sys.stdin)
    if p.returncode == 0:
        sys.stdout.write("Process finished with code 0\n")
    else:
        key = os.environ["CRASHME_KEY"]
        msg = challenge + ":" + str(datetime.datetime.now())
        sig = hmac.new(key.encode("utf8"), msg=msg.encode("utf8")).hexdigest()
        sys.stdout.write("FLAG{" + msg + ":" + sig + "}\n")
