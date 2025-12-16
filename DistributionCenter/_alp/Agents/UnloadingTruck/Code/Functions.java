String getText()
{/*ALCODESTART::1421133435283*/
return capacity - processedPallets + " / " + capacity;
/*ALCODEEND*/}

boolean unloadPallet()
{/*ALCODESTART::1422814591668*/
processedPallets++;
return processedPallets == capacity;
/*ALCODEEND*/}

