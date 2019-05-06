
import gevent
from gevent import monkey
monkey.patch_all()

import time
import smtplib

TEST_MAIL ="""
Date: Wed, 30 Jul 2014 03:29:50 +0800 (CST)
From: =?utf-8?B?6IGU5oOz?= <client@gsmtpd.org>
To: test@gsmtpd.org
Message-ID: <766215193.1675381406662190229.JavaMail.root@USS-01>
Subject: =?utf-8?B?6IGU5oOz56e75Yqo5LqS6IGU572R5pyN5Yqh5rOo5YaM56Gu6K6k6YKu5Lu2?=
MIME-Version: 1.0
Content-Type: multipart/mixed; 
        boundary="----=_Part_335076_1490382245.1406662190222"

------=_Part_335076_1490382245.1406662190222
Content-Type: multipart/related; 
        boundary="----=_Part_335077_605133107.1406662190222"

------=_Part_335077_605133107.1406662190222
Content-Type: text/html;charset=utf-8
Content-Transfer-Encoding: quoted-printable

 <html><head></head><body>=E5=B0=8A=E6=95=AC=E7=9A=84=E7=94=A8=E6=88=B7=EF=
=BC=9A<br/>=E6=82=A8=E5=A5=BD=EF=BC=81<br/>=E8=AF=B7=E7=82=B9=E5=87=BB=E8=
=81=94=E6=83=B3=E5=B8=90=E5=8F=B7=E7=A1=AE=E8=AE=A4=E9=93=BE=E6=8E=A5=EF=BC=
=8C=E4=BB=A5=E6=A0=A1=E9=AA=8C=E6=82=A8=E7=9A=84=E8=81=94=E6=83=B3=E5=B8=90=
=E5=8F=B7=EF=BC=9A<br/><a href=3D"https://passport.lenovo.com/wauthen/verif=
yuser?username=3D&vc=3DuHwf&accountid=3D1358934&lenovoid.=
cb=3D&lenovoid.realm=3Dthinkworld.lenovo.com&lang=3Dzh_CN&display=3D&lenovo=
id.ctx=3D&lenovoid.action=3D&lenovoid.lang=3D&lenovoid.uinfo=3D&lenovoid.vp=
=3D&verifyFlag=3Dnull">https://passport.lenovo.com/wauthen/verifyuser?usern=
ame=3o.org&vc=3DuHwf&accountid=3&lenovoid.cb=3D&lenov=
oid.realm=3Dthinkworld.lenovo.com&lang=3Dzh_CN&display=3D&lenovoid.ctx=3D&l=
enovoid.action=3D&lenovoid.lang=3D&lenovoid.uinfo=3D&lenovoid.vp=3D&verifyF=
lag=3Dnull</a><br/>=EF=BC=88=E5=A6=82=E6=9E=9C=E4=B8=8A=E9=9D=A2=E7=9A=84=
=E9=93=BE=E6=8E=A5=E6=97=A0=E6=B3=95=E7=82=B9=E5=87=BB=EF=BC=8C=E6=82=A8=E4=
=B9=9F=E5=8F=AF=E4=BB=A5=E5=A4=8D=E5=88=B6=E9=93=BE=E6=8E=A5=EF=BC=8C=E7=B2=
=98=E8=B4=B4=E5=88=B0=E6=82=A8=E6=B5=8F=E8=A7=88=E5=99=A8=E7=9A=84=E5=9C=B0=
=E5=9D=80=E6=A0=8F=E5=86=85=EF=BC=8C=E7=84=B6=E5=90=8E=E6=8C=89=E2=80=9C=E5=
=9B=9E=E8=BD=A6=E2=80=9D=E9=94=AE)=E3=80=82<br/>=E6=9D=A5=E8=87=AA=E8=81=94=
=E6=83=B3=E5=B8=90=E5=8F=B7</body></html>
------=_Part_335077_605133107.1406662190222--

------=_Part_335076_1490382245.1406662190222--
"""

def timeit(func):

    def wrap(num, port, *args, **kwargs):
        
        max_rqs = 0
        for _ in xrange(3):

            conns = [smtplib.SMTP(port=port) for x in xrange(num)] 
            map(lambda x: x.connect('127.0.0.1', port), conns)

            start_at = time.time()
            func(num, conns, **kwargs)
            interval = time.time() - start_at
            for con in conns:
                try:
                    con.quit()
                    con.close()
                except Exception:
                    pass
            gevent.sleep(3)
            rqs = num/interval
            max_rqs = max(rqs, max_rqs)
        return max_rqs
    return wrap

@timeit
def helo(num, conns):

    tasks = [gevent.spawn(x.helo) for x in conns]
    gevent.joinall(tasks)

@timeit
def send(num, conns):

    tasks = [gevent.spawn(x.sendmail, 'r@r.com',['test@test.org'], TEST_MAIL) for x in conns]
    gevent.joinall(tasks)


def main(port, num):
    
    print "%d %s %s"% (num, helo(num, port), send(num, port) )


if __name__ == '__main__':
    import sys
    try:
        main(int(sys.argv[1]), int(sys.argv[2]))
    except IndexError:
        print 'python concurrency.py <port> <connection number>'
