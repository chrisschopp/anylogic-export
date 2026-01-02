Pallet getPallet(Order order)
{/*ALCODESTART::1417693092940*/
for (Storage st : storageSystem.storages) {
	var freePallet = (Pallet) findFirst(st.getAgents(), cp -> !((Pallet)cp).reserved);
	if (freePallet != null) {
		freePallet.reserved = true;
		return freePallet;
	}
}
return null;
/*ALCODEEND*/}
