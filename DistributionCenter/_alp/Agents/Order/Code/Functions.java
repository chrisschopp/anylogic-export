int findType(int index)
{/*ALCODESTART::1422203690663*/
int cumsum = capacities[0];
int type = 0;
while (cumsum <= index) {
	type++;
	cumsum += capacities[type];
} 
return type;
/*ALCODEEND*/}

int palletsToAssemble()
{/*ALCODESTART::1422821300583*/
return size - pallets.size();
/*ALCODEEND*/}

