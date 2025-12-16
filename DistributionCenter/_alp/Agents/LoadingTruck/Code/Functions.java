int getOrdersCapacity()
{/*ALCODESTART::1421133357182*/
int cap = 0;
for (Order order : orders) {
	cap = cap + order.size;
}	
return cap;
/*ALCODEEND*/}

String getText()
{/*ALCODESTART::1421133418163*/
return processedPallets + " / " + getOrdersCapacity();
/*ALCODEEND*/}

boolean loadPallet()
{/*ALCODESTART::1422819925333*/
processedPallets++;
return getOrdersCapacity() == processedPallets;
/*ALCODEEND*/}

