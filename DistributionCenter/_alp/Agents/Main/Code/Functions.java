Order nextOrderForAssembling()
{/*ALCODESTART::1412920085411*/
int assembling = orders.waitAssembling() + orders.assembling();
if (assembling > 60) return null;

for (Order order : queue) {
	if (!order.inState(order.waitAtQueue)) continue;
	if (findDock(order) == null) continue;
	if (!enoughPalletsForOrder(order)) continue;
	return order;
}
return null;
/*ALCODEEND*/}

boolean enoughPalletsForOrder(Order order)
{/*ALCODESTART::1412928177922*/
for (int i = 0; i < palletTypesNum; i++) {
	if (order.capacities[i] > types.get(i).storageSystem.nFreeCells())
		return false;
}
return true;
/*ALCODEEND*/}

double moveFromStorageToDock(Dock dock)
{/*ALCODESTART::1413738420219*/
for (Iterator<Order> it = standByStorage.orders.iterator(); it.hasNext();) {
    Order order = it.next();
	if (dock.spaceAvailable() < order.size)
		continue;

	for (Pallet p : order.pallets)
		dock.reserve(p);

	//send order to dock
	it.remove();
	for (Iterator<Pallet> itp = order.pallets.iterator(); itp.hasNext();) {
		Pallet p = itp.next();
		itp.remove();
		p.dock = dock;
		enterToDock.take(p);
	}
}
/*ALCODEEND*/}

Dock findDockToLoadTruck(LoadingTruck truck)
{/*ALCODESTART::1413761394214*/
Dock best = null;
int bestCapacity = 0;
for(Dock dock : loadDocks) {
	if( dock.orders.size() == 0 )
		continue;
	if( dock.isOccupied )
		continue;

	int ordersCapacity = 0;
	for( Order order : dock.orders ) {
		if( order.size > truckCapacity )
			continue;
		ordersCapacity += order.size;
	}

	if ( ordersCapacity > bestCapacity ) {
		if( ordersCapacity >= 0.5 * truckCapacity ) {
			bestCapacity = ordersCapacity;
			best = dock;
		}
	}
}

return best;
/*ALCODEEND*/}

void switchCamera()
{/*ALCODESTART::1413886090309*/
cameraIdx = (cameraIdx + 1) % cameras.size();
window3d.setCamera(cameras.get(cameraIdx), true, 5000);
/*ALCODEEND*/}

double createTypes(int num)
{/*ALCODESTART::1417696899586*/
int nRowsHalf = storagePools.size();
int idx = nRowsHalf - 1;
for (int i = 0; i < num; i++) {
	Type type = add_types(i);
	StorageSystem<Pallet> system = storagePools.get(i);
	typeStoragePools.put(type, system);
	type.storageSystem = system;
	for (int j = i; j < nRowsHalf; j += num) {
		Storage st = storages.get(idx--);
		system.addStorage(st);
	}
}
/*ALCODEEND*/}

Type findType(int typeID)
{/*ALCODESTART::1417769272907*/
Type res = null;
for (Type t : types) {
	if (t.id == typeID) {
		res = t;
		break;
	}
}
return res;
/*ALCODEEND*/}

double findOrdersForLoading(Dock dock,LoadingTruck truck)
{/*ALCODESTART::1418205824234*/
int tcap = truck.capacity;
for (Order order : dock.orders) {
	if (tcap >= order.size) {
		truck.orders.add(order);
	 	tcap -= order.size;
		for (Pallet p : order.pallets) {
			p.truck = truck;
			startLoading.take(p);
		}
	}
}
/*ALCODEEND*/}

double[] getWeights()
{/*ALCODESTART::1418333908921*/
double[] weights = new double[palletTypesNum];
for (int i = 0; i < palletTypesNum; i++) {
	weights[i] = 10 + max(0, types.get(i).claimed - types.get(i).storageSystem.size());
}
return weights;
/*ALCODEEND*/}

boolean chooseForkliftForDock(Dock dock,Forklift unit,int forkliftLimit)
{/*ALCODESTART::1418651296985*/
if (unit.inUse)
	return dock.processingForklift == unit;

if (dock.processingForklift != null)
	return false;

if (dock.releaseUnused(unit, forkliftLimit))
	return false;

if (dock.seizeForklift(unit, forkliftLimit)) {
	dock.processingForklift = unit;
	return true;
}

return false;
/*ALCODEEND*/}

boolean continueMoving(Pallet pallet,Forklift unit)
{/*ALCODESTART::1418651296989*/
if (!unit.inUse
	|| pallet.seizedForklift == null) {
	return false;
} else return pallet.seizedForklift == unit;
/*ALCODEEND*/}

boolean chooseForkliftsForMove(Pallet pallet,Forklift unit,int forkliftLimit,ResourceHandler target)
{/*ALCODESTART::1418712702952*/
if (unit.inUse || pallet.seizedForklift != null)
	return false;

if (target.releaseUnused(unit, forkliftLimit))
	return false;

if (target.seizeForklift(unit, forkliftLimit)) {
	pallet.seizedForklift = unit;
	return true;
}

return false;


/*ALCODEEND*/}

Pallet spawnInitialPalletes(double level)
{/*ALCODESTART::1418767848493*/
for (Type t : types) {
	int count = (int)(t.storageSystem.capacity() * level);
	for (int i = 0; i < count; i++)
		enter.take(new Pallet(t.id, t));
}
/*ALCODEEND*/}

double createOrder(int[] capacities,boolean addToHead)
{/*ALCODESTART::1418771161643*/
if (lastOrderId == 0)
	typeChartHandle();
if (lastOrderId == 9999)
	lastOrderId = 0;


int s = 0;
for( int capacity : capacities)
	s += capacity;

Order order = add_orders(s, lastOrderId++);
order.capacities = new int[capacities.length];
for (int i = 0; i < capacities.length; i++){
	order.capacities[i] = capacities[i];
}

if (addToHead) queue.add(0, order);
else queue.add(order);

for (int i = 0; i < palletTypesNum; i++) {
	types.get(i).claimed += order.capacities[i];
}
/*ALCODEEND*/}

double getControlY()
{/*ALCODESTART::1418985611471*/
if (selectedViewArea == view3D) return -600;
if (selectedViewArea == viewMetrics) return -1600;
else return -2500;
/*ALCODEEND*/}

int discrete(double[] weights)
{/*ALCODESTART::1418990159502*/
double[] vals = new double[palletTypesNum];
for (int i = 0; i < palletTypesNum; i++)
	vals[i] = i;

CustomDistributionDiscrete distribution = new CustomDistributionDiscrete(vals, weights, this.getDefaultRandomGenerator());

return distribution.get().intValue();

/*ALCODEEND*/}

Dock findDock(Order order)
{/*ALCODESTART::1418999565450*/
if (order == null) return null;
Dock best = null;
for (Dock dock : loadDocks) {
	int spaceAvailable = dock.spaceAvailable();
	if (spaceAvailable >= order.size
		&& (best == null || spaceAvailable >= best.spaceAvailable())) {
		best = dock;
	}
}
if (best == null
	&& standByStorage.spaceAvailable() >= order.size )
		best = standByStorage;

return best;
/*ALCODEEND*/}

double typeChartHandle()
{/*ALCODESTART::1419159239375*/
for( int i = 1; i < palletTypesNum; i++ ) {
	amountOfPalletsForEachType.addDataItem(new DataItem() {
			private int color;

			@Override
			public void update() {
				this.setValue(typesSizes(color));
			}

			DataItem setColor(int c) {
				color = c;
				return this;
			}
		}.setColor(i), "", colors(i));
}
/*ALCODEEND*/}

int typesSizes(int id)
{/*ALCODESTART::1419326909312*/
return types.get(id).storageSystem.size();
/*ALCODEEND*/}

double setInitialCapacities()
{/*ALCODESTART::1419334669389*/
int capacity = maxOrderSize;
while (capacity > 0) {
		int i = uniform_discr(0, palletTypesNum - 1);
		int c = uniform_discr(0, capacity);
		orderCapacities[i] += c;
		capacity -= c;
}
/*ALCODEEND*/}

double increaseCapacity(int index)
{/*ALCODESTART::1419334771377*/
if (sumCapacities() < maxOrderSize)
	orderCapacities[index]++;
/*ALCODEEND*/}

double decreaseCapacity(int i)
{/*ALCODESTART::1419334802753*/
if (sumCapacities() > minOrderSize  && orderCapacities[i] > 0)
	orderCapacities[i]--;

/*ALCODEEND*/}

int sumCapacities()
{/*ALCODESTART::1419334829094*/
int sum = 0;
for (int i : orderCapacities)
	sum += i;
return sum;
/*ALCODEEND*/}

boolean checkUnloadAnyMoving()
{/*ALCODESTART::1422101513512*/
boolean unloadAnyMoving = toUnloadStart.isBlocked() || fromUnloadStart.isBlocked();
if (unloadWaitMoving.size() == 0 || unloadAnyMoving)
	return false;

UnloadingTruck truck = unloadWaitMoving.get(0);
if (truck.processedPallets > 0) { // move from dock
	holdFromUnload.unblock();
} else { // move to dock
	holdToUnload.unblock();
}

return true;


/*ALCODEEND*/}

boolean checkLoadAnyMoving()
{/*ALCODESTART::1422128574185*/
boolean loadAnyMoving = toLoadStart.isBlocked() || fromLoadStart.isBlocked();
if (loadWaitMoving.size() == 0 || loadAnyMoving)
	return false;

LoadingTruck truck = loadWaitMoving.get(0);

if (truck.processedPallets > 0) { // move from dock
	holdFromLoad.unblock();
} else { // move to dock
	holdToLoad.unblock();
}
return true;


/*ALCODEEND*/}

double recalculateWaitForRackSystem()
{/*ALCODESTART::1422145022040*/
LinkedHashSet<Pallet> palletToFree = new LinkedHashSet<>();
for (Pallet p : waitForRackSystem) {
	if (p.type.storageSystem.nFreeCells() >= p.type.reservedCells) {
		palletToFree.add(p);
		p.type.reservedCells++;
	}
}

for (Pallet p : palletToFree) {
	waitForRackSystem.free(p);
}
/*ALCODEEND*/}

double recalculateWaitForDockStorage()
{/*ALCODESTART::1422146268259*/
LinkedHashSet<UnloadingTruck> truckToFree = new LinkedHashSet<>();
for (UnloadingTruck t : waitForDockStorage) {
	if (t.capacity <= t.dock.spaceAvailable()) {
		truckToFree.add(t);
	}
}

for (UnloadingTruck t : truckToFree) {
	waitForDockStorage.free(t);
}
/*ALCODEEND*/}

double navigate(ViewArea viewArea)
{/*ALCODESTART::1489390965545*/
selectedViewArea = viewArea;
viewArea.navigateTo();
groupMainMenu.setPos( viewArea.getX(), viewArea.getY() );
/*ALCODEEND*/}

Color colors(int index)
{/*ALCODESTART::1553678256567*/
return colorSamples.get(index).getFillColor();
/*ALCODEEND*/}
