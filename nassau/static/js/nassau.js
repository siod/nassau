
var classLookup = ["default","info","danger","success"];
function populateTable(tableId,data,mapping) {
	var tbody = $('#' + tableId + ' tbody');
	for (var i = 0;i < data.length; ++i) {
		var row = document.createElement('tr');
		row.className = classLookup[data[i].status];
		for (var x in mapping) {
			var col = document.createElement('td');
			col.innerHTML = data[i][mapping[x]];
			row.appendChild(col);
		}
		tbody.append(row);
	}
}

