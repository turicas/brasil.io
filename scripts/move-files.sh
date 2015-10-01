#!/bin/bash

for filename in topo/*; do
	uf=$(echo $filename | sed 's/topo\///; s/-.*//');
	newfilename=$(echo $filename | sed 's/.*-//; s/.json/.topo.json/');
	mv $filename $uf/$newfilename;
done

for filename in geo/*; do
	uf=$(echo $filename | sed 's/geo\///; s/-.*//');
	newfilename=$(echo $filename | sed 's/.*-//; s/.json/.geo.json/');
	mv $filename $uf/$newfilename;
done
