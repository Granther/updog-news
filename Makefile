run:
	python3.11 run.py

run default:
	python run.py

lint:
	python3.11 -m pylint --disable=C,R,W,F app

lint super:
	python3.11 -m pylint --disable=C,R,W,F app/superintend

