rm -f hin? hout? lan?
rm -f rout?
python host.py 0 0 sender 20 20 &
python router.py 0 0 1 &
python router.py 1 1 2 &
python controller.py host 0 1 router 0 1 lan 0 1 2 &
