void createOrderEvent()
{/*ALCODESTART::1412862545035*/
if( orders.size()  < ordersListMaxLength ) {
	int capacity = uniform_discr(minOrderSize,
								 maxOrderSize);
	int[] capacities = new int[palletTypesNum];

	while (capacity > 0) {
		int i = uniform_discr(0, palletTypesNum - 1);
		int c = uniform_discr(0, capacity);
		capacities[i] += c;
		capacity -= c;
	}

	createOrder(capacities, false);
}
/*ALCODEEND*/}

void maybeStartAssembling()
{/*ALCODESTART::1418295603347*/
Order order = nextOrderForAssembling();

if (order != null) {
	Dock dock = findDock(order);
	send("waitAssembling", order);
	for (int i = 0; i < palletTypesNum; i++) {
		Type t = types.get(i);
		t.claimed -= order.capacities[i];
		for (int j = 0; j < order.capacities[i]; j++) {
			Pallet p = t.getPallet(order);
			dock.reserve(p);
			p.order = order;
			p.dock = dock;
			enterPallet.take(p);
		}
	}
}
/*ALCODEEND*/}

void hideCheck()
{/*ALCODESTART::1419340883039*/
groupCheck.setVisible(false);
exclamation.setVisible(false);
/*ALCODEEND*/}
