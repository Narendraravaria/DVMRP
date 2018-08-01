rm -f lan? hout? hin?
rm -f rout?
python router.py 0 0 1 &
python router.py 1 1 2 &
python router.py 2 2 3 &
python router.py 3 3 0 &
python controller.py host router 0 1 2 3 lan 0 1 2 3 &
