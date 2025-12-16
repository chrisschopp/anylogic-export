boolean seizeForklift(Forklift unit,int limit)
{/*ALCODESTART::1422816709017*/
if (usedForklifts.size() < limit 
	|| usedForklifts.contains(unit)) {
	unit.inUse = true;
	usedForklifts.add(unit);
	return true;
}

return false;
/*ALCODEEND*/}

double releaseForklift(Forklift unit)
{/*ALCODESTART::1422816709019*/
unit.inUse = false;
usedForklifts.remove(unit);
/*ALCODEEND*/}

boolean releaseUnused(Forklift unit,int limit)
{/*ALCODESTART::1422816709021*/
if (usedForklifts.size() > limit) {
	if (usedForklifts.contains(unit))
		releaseForklift(unit);
	return true;	
}

return false;
/*ALCODEEND*/}

