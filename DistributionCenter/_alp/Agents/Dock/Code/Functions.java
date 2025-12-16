double releaseForklift(Forklift unit)
{/*ALCODESTART::1418676718441*/
if (unit == null)
  unit = processingForklift;
if (processingForklift == unit)
  processingForklift = null;
super.releaseForklift(unit);
/*ALCODEEND*/}

int spaceAvailable()
{/*ALCODESTART::1418991198976*/
return storage.capacity() - storage.size() - reserved.size();
/*ALCODEEND*/}

double reserve(Pallet p)
{/*ALCODESTART::1422182736219*/
reserved.add(p);
/*ALCODEEND*/}

double unreserve(Pallet p)
{/*ALCODESTART::1422182786794*/
reserved.remove(p);
/*ALCODEEND*/}

