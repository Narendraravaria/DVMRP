rm -f hin? hout? lan?
rm -f rout?
python host.py 0 0 sender 30 10 &
python host.py 1 1 receiver &
python host.py 2 2 receiver &
python router.py 0 0 1 &
python router.py 1 1 2 &
python router.py 2 2 3 &
python router.py 3 3 0 &
python controller.py host 0 1 2 router 0 1 2 3 lan 0 1 2 3 &
