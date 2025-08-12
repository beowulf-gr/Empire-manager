document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Read All Data from the HTML Data Hub ---
    const gameData = document.getElementById('game-data').dataset;
    const realmInfo = document.getElementById('realm-info').dataset;

    const realmName = gameData.realmName;
    const csrfToken = gameData.csrfToken;
    const currentTreasury = parseFloat(realmInfo.treasury);

    const previewUrl = gameData.previewUrl;
    const idlePopUrl = gameData.idlePopUrl;
    const landUnitsUrl = gameData.landUnitsUrl;
    const strongholdTypesUrl = gameData.strongholdTypesUrl;
    const roadEligibleUrl = gameData.roadEligibleUrl;
    const mineEligibleUrl = gameData.mineEligibleUrl;
    const resourceTypesUrl = gameData.resourceTypesUrl; // Assuming you add this to the data hub
    const goodsTypesUrl = gameData.goodsTypesUrl;     // Assuming you add this to the data hub

    // --- 2. Global DOM Element References ---
    const actionButtons = document.querySelectorAll('.action-button');
    const actionDetailsLinks = document.querySelectorAll('.action-details-link');
    const unifiedActionModal = document.getElementById('unified-action-modal');
    const closeButton = unifiedActionModal.querySelector('.close-button');
    const modalTitle = document.getElementById('modal-title');
    const modalDescription = document.getElementById('modal-description');
    const dynamicActionForm = document.getElementById('dynamic-action-form');
    const formActionType = document.getElementById('form-action-type');
    const dynamicInputsDiv = document.getElementById('dynamic-inputs');
    const formSubmitButton = document.getElementById('form-submit-button');
    const endSeasonBtn = document.getElementById('end-season-btn');
    const availableActionsData = JSON.parse(document.getElementById('available-actions-data').textContent);

    let allIdlePopulation = [], allGoodsTypesData = [], allResourcesData = [];

    const actionsMap = new Map();
    availableActionsData.forEach(action => {
        actionsMap.set(action.name, action);
        actionsMap.set(action.action_key, action);
    });

    // --- 3. Helper Functions ---
    async function fetchSelectOptions(url, selectElement) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            const firstOptionHTML = selectElement.options[0]?.outerHTML || '<option value="" disabled selected>Select an option</option>';
            selectElement.innerHTML = firstOptionHTML;
            data.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.id;
                opt.textContent = option.name || option.display_name;
                if (option.has_stronghold !== undefined) { opt.dataset.hasStronghold = option.has_stronghold; }
                if (url.includes('get_resource_types_json')) { allResourcesData.push({ ...option, value_numeric: parseFloat(option.value) }); }
                else if (url.includes('get_goods_types_json')) { allGoodsTypesData.push({ ...option, value_numeric: parseFloat(option.value) }); }
                selectElement.appendChild(opt);
            });
            return data;
        } catch (error) { console.error(`Error fetching options from ${url}:`, error); return []; }
    }


    function updatePopulationDropdowns() {
        const popSelects = document.querySelectorAll('.population-select');
        const selectedValues = new Set();
        popSelects.forEach(select => { if (select.value) selectedValues.add(select.value); });
        popSelects.forEach(select => {
            const currentSelection = select.value;
            for (const option of select.options) {
                if (!selectedValues.has(option.value) || option.value === currentSelection) option.style.display = '';
                else option.style.display = 'none';
            }
        });
    }

    function updateLandUnitDropdowns() {
        const landUnitSelects = document.querySelectorAll('.road-land-unit-select');
        const selectedValues = new Set();
        landUnitSelects.forEach(select => { if (select.value) selectedValues.add(select.value); });
        landUnitSelects.forEach(select => {
            const currentSelection = select.value;
            for (const option of select.options) {
                if (!option.value) continue;
                if (!selectedValues.has(option.value) || option.value === currentSelection) option.style.display = '';
                else option.style.display = 'none';
            }
        });
    }

    function displayCostPreview(costs) {
        const previewContainer = document.getElementById('cost-preview-container');
        if (!previewContainer) return;
        let html = '<h4>Total Cost:</h4><ul>';
        let hasCosts = false;
        if (costs && typeof costs === 'object') {
            for (const [key, value] of Object.entries(costs)) {
                if (value > 0) {
                    html += `<li>${key.charAt(0).toUpperCase() + key.slice(1)}: ${value}</li>`;
                    hasCosts = true;
                }
            }
        }
        if (!hasCosts) { html = ''; } else { html += '</ul>'; }
        previewContainer.innerHTML = html;
    }

    async function buildGenericInputs(action, containerDiv) {
        containerDiv.innerHTML = '';
        if (!action.inputs) return;
        for (const inputDef of action.inputs) {
            let htmlContent = `<label for="${inputDef.name}">${inputDef.label}</label>`;
            if (inputDef.type === 'select') {
                htmlContent += `<select id="${inputDef.name}" name="${inputDef.name}" ${inputDef.required ? 'required' : ''}></select>`;
            } else {
                htmlContent += `<input type="${inputDef.type || 'text'}" id="${inputDef.name}" name="${inputDef.name}" value="${inputDef.default || ''}" ${inputDef.required ? 'required' : ''}>`;
            }
            htmlContent += '<br><br>';
            containerDiv.innerHTML += htmlContent;
        }
        for (const inputDef of action.inputs) {
            if (inputDef.type === 'select') {
                const selectElement = document.getElementById(inputDef.name);
                let url = inputDef.options_url.replace('placeholder', realmName);
                await fetchSelectOptions(url, selectElement);
            }
        }
    }

    // --- MAIN EVENT LISTENER ---
    actionButtons.forEach(button => {
        button.addEventListener('click', async function(event) {
            const actionKey = this.getAttribute('data-action-slug');
            const action = actionsMap.get(actionKey);
            if (!action) return;

            modalTitle.textContent = action.name;
            modalDescription.textContent = action.description;
            formActionType.value = action.action_key;
            formSubmitButton.textContent = action.submit_text;
            formSubmitButton.style.display = 'block';
            formSubmitButton.disabled = false;
            
            const idlePopRes = await fetch(idlePopUrl);
            allIdlePopulation = await idlePopRes.json();

            if (actionKey === 'construct_stronghold' || actionKey === 'build_roads' || actionKey === 'build_mine') {
                dynamicInputsDiv.innerHTML = `
                    <div id="form-inputs-container"></div>
                    <div id="cost-preview-container" style="margin-top: 15px; padding: 10px; border: 1px solid #eee;"></div>`;
                const formInputsContainer = document.getElementById('form-inputs-container');

                if (actionKey === 'construct_stronghold') {
                    dynamicInputsDiv.innerHTML = `
                        <div id="form-inputs-container">
                            <label for="stronghold_type">Stronghold Type:</label>
                            <select id="stronghold_type" name="stronghold_type" required></select><br><br>
                            <label for="land_unit">Location:</label>
                            <select id="land_unit" name="land_unit" required></select><br><br>
                            <label for="stronghold_name">Name (Optional):</label>
                            <input type="text" id="stronghold_name" name="stronghold_name"><br><br>
                            <div id="population-dropdown-container"></div>
                        </div>
                        <div id="cost-preview-container" style="margin-top: 15px; padding: 10px; border: 1px solid #eee;"></div>
                    `;
                    const strongholdSelect = document.getElementById('stronghold_type');
                    const landUnitSelect = document.getElementById('land_unit');
                    const popContainer = document.getElementById('population-dropdown-container');
                    await fetchSelectOptions(strongholdTypesUrl, strongholdSelect);
                    await fetchSelectOptions(landUnitsUrl, landUnitSelect);
                    strongholdSelect.addEventListener('change', async function() {
                        const strongholdId = this.value;
                        popContainer.innerHTML = '';
                        if (!strongholdId) { displayCostPreview({}); return; }
                        const response = await fetch(previewUrl, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                            body: JSON.stringify({
                                action_key: 'construct_stronghold',
                                stronghold_type_id: strongholdId
                            })
                        });
                        const costs = await response.json();
                        displayCostPreview(costs);
                        const requiredPop = costs.population || 0;
                        if (allIdlePopulation.length < requiredPop) {
                            popContainer.innerHTML = `<p style="color: red;">Not enough idle population!</p>`;
                            formSubmitButton.disabled = true;
                        } else {
                            formSubmitButton.disabled = false;
                            popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;
                            for (let i = 0; i < requiredPop; i++) {
                                const newSelect = document.createElement('select');
                                newSelect.name = 'assigned_population'; newSelect.className = 'population-select'; newSelect.required = true;
                                newSelect.innerHTML = '<option value="" selected>-- Select a Unit --</option>';
                                allIdlePopulation.forEach(unit => { newSelect.innerHTML += `<option value="${unit.id}">${unit.display_name}</option>`; });
                                popContainer.appendChild(newSelect);
                                newSelect.addEventListener('change', updatePopulationDropdowns);
                            }
                        }
                    });
                    displayCostPreview({});
                } else if (actionKey === 'build_roads') {
                    dynamicInputsDiv.innerHTML = `
                        <div id="form-inputs-container">
                            <p>Select up to 4 land units (at least 1 is required):</p>
                            <div id="land-unit-dropdowns"></div>
                            <div id="population-dropdown-container"></div>
                        </div>
                        <div id="cost-preview-container" style="margin-top: 15px; padding: 10px; border: 1px solid #eee;"></div>
                    `;
                    const landUnitContainer = document.getElementById('land-unit-dropdowns');
                    const popContainer = document.getElementById('population-dropdown-container');
                    const landUnitsRes = await fetch(roadEligibleUrl);
                    const landUnits = await landUnitsRes.json();
                    for (let i = 0; i < 4; i++) {
                        const select = document.createElement('select');
                        select.name = 'land_units_for_roads'; select.className = 'road-land-unit-select';
                        if (i === 0) { select.required = true; select.innerHTML = '<option value="" disabled selected>-- Select Unit #1 --</option>'; } 
                        else { select.innerHTML = `<option value="">-- Optional Unit #${i + 1} --</option>`; }
                        landUnits.forEach(unit => { select.innerHTML += `<option value="${unit.id}" data-has-stronghold="${unit.has_stronghold}">${unit.name}</option>`; });
                        landUnitContainer.appendChild(select);
                        select.addEventListener('change', updateLandUnitDropdowns);
                    }
                    const recalculateRoadsCost = async () => {
                        const selectedOptions = document.querySelectorAll('.road-land-unit-select option:checked');
                        let selected_land_ids = [];
                        selectedOptions.forEach(opt => { if (opt.value) selected_land_ids.push(opt.value); });
                        const response = await fetch(previewUrl, {
                            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                            body: JSON.stringify({ action_key: 'build_roads', land_unit_ids: selected_land_ids })
                        });
                        const costs = await response.json();
                        displayCostPreview(costs);
                        const requiredPop = costs.population || 0;
                        popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;
                        if (allIdlePopulation.length < requiredPop) {
                            popContainer.innerHTML += `<p style="color: red;">Not enough idle population!</p>`;
                            formSubmitButton.disabled = true;
                        } else {
                            formSubmitButton.disabled = false;
                            for (let i = 0; i < requiredPop; i++) {
                                const newSelect = document.createElement('select');
                                newSelect.name = 'assigned_population'; newSelect.className = 'population-select'; newSelect.required = true;
                                newSelect.innerHTML = '<option value="" selected>-- Select a Unit --</option>';
                                allIdlePopulation.forEach(unit => { newSelect.innerHTML += `<option value="${unit.id}">${unit.display_name}</option>`; });
                                popContainer.appendChild(newSelect);
                                newSelect.addEventListener('change', updatePopulationDropdowns);
                            }
                        }
                    };
                    landUnitContainer.addEventListener('change', recalculateRoadsCost);
                    recalculateRoadsCost();
                } else if (actionKey === 'build_mine') {
                    dynamicInputsDiv.innerHTML = `
                        <div id="form-inputs-container">
                            <label for="land_unit_for_mine">Select Land Unit:</label>
                            <select id="land_unit_for_mine" name="land_unit_for_mine" required></select><br><br>
                            <div id="population-dropdown-container"></div>
                        </div>
                        <div id="cost-preview-container" style="margin-top: 15px; padding: 10px; border: 1px solid #eee;"></div>
                    `;
                    const landUnitSelect = document.getElementById('land_unit_for_mine');
                    const popContainer = document.getElementById('population-dropdown-container');
                    await fetchSelectOptions(mineEligibleUrl, landUnitSelect);
                    const response = await fetch(previewUrl, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                            body: JSON.stringify({
                                action_key: 'build_mine',
                            })
                        });
                        const costs = await response.json();
                    displayCostPreview(costs);
                    const requiredPop = costs.population || 1;
                    popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;
                    if (allIdlePopulation.length < requiredPop) {
                        popContainer.innerHTML += `<p style="color: red;">Not enough idle population!</p>`;
                        formSubmitButton.disabled = true;
                    } else {
                        formSubmitButton.disabled = false;
                        const newSelect = document.createElement('select');
                        newSelect.name = 'assigned_population'; newSelect.className = 'population-select'; newSelect.required = true;
                        newSelect.innerHTML = '<option value="" selected>-- Select a Unit --</option>';
                        allIdlePopulation.forEach(unit => { newSelect.innerHTML += `<option value="${unit.id}">${unit.display_name}</option>`; });
                        popContainer.appendChild(newSelect);
                    }
                } else if (actionKey === "upgrade_stronghold") {
                    // Create containers programmatically for robustness
                    const formInputsContainer = document.createElement('div');
                    const costPreviewContainer = document.createElement('div');
                    costPreviewContainer.id = 'cost-preview-container';
                    costPreviewContainer.style.cssText = "margin-top: 15px; padding: 10px; border: 1px solid #eee;";

                    // --- 1. Create the First Dropdown (Stronghold Selection) ---
                    const strongholdLabel = document.createElement('label');
                    strongholdLabel.textContent = "Select Stronghold:";
                    const strongholdSelect = document.createElement('select');
                    strongholdSelect.id = 'stronghold_to_upgrade';
                    strongholdSelect.name = 'stronghold_to_upgrade';
                    strongholdSelect.required = true;

                    formInputsContainer.appendChild(strongholdLabel);
                    formInputsContainer.appendChild(strongholdSelect);
                    formInputsContainer.appendChild(document.createElement('br'));
                    formInputsContainer.appendChild(document.createElement('br'));

                    // --- 2. Create Containers for the Dynamic Elements ---
                    const upgradeContainer = document.createElement('div');
                    upgradeContainer.id = 'upgrade-choice-container';
                    upgradeContainer.style.display = 'none'; // Initially hidden
                    const popContainer = document.createElement('div');
                    popContainer.id = 'population-dropdown-container';

                    formInputsContainer.appendChild(upgradeContainer);
                    formInputsContainer.appendChild(popContainer);
                    
                    dynamicInputsDiv.appendChild(formInputsContainer);
                    dynamicInputsDiv.appendChild(costPreviewContainer);

                    // --- 3. Populate First Dropdown ---
                    await fetchSelectOptions(gameData.existingStrongholdsUrl, strongholdSelect);

                    // --- 4. Attach Event Listener to First Dropdown ---
                    strongholdSelect.addEventListener('change', async function() {
                        const strongholdId = this.value;
                        upgradeContainer.innerHTML = ''; // Clear previous upgrade dropdown
                        popContainer.innerHTML = '';
                        displayCostPreview({});
                        if (!strongholdId) return;

                        // Create the second dropdown (Upgrade Selection)
                        upgradeContainer.innerHTML = `
                            <label for="upgrade_type">Select Improvement:</label>
                            <select id="upgrade_type" name="upgrade_type" required></select><br><br>
                        `;
                        const upgradeSelect = document.getElementById('upgrade_type');
                        
                        await fetchSelectOptions(`/realm/get_available_upgrades_json/${strongholdId}/`, upgradeSelect);
                        upgradeContainer.style.display = 'block';

                        // Attach listener to the newly created upgrade dropdown
                        upgradeSelect.addEventListener('change', async function() {
                            const upgradeId = this.value;
                            popContainer.innerHTML = '';
                            if (!upgradeId) { displayCostPreview({}); return; }
                            
                            const detailsRes = await fetch(`/realm/get_upgrade_details_json/${upgradeId}/`);
                            const details = await detailsRes.json();
                            
                            let costs = { ...details.resource_costs, 'Gold': details.gold_cost, 'Population': details.population_cost };
                            displayCostPreview(costs);

                            const requiredPop = details.population_cost;
                            if (allIdlePopulation.length < requiredPop) {
                                popContainer.innerHTML = `<p style="color: red;">Not enough idle population!</p>`;
                                formSubmitButton.disabled = true;
                            } else {
                                formSubmitButton.disabled = false;
                                popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;
                                for (let i = 0; i < requiredPop; i++) {
                                    const newSelect = document.createElement('select');
                                    newSelect.name = 'assigned_population';
                                    newSelect.className = 'population-select';
                                    newSelect.required = true;
                                    newSelect.innerHTML = '<option value="" selected>-- Select a Unit --</option>';
                                    allIdlePopulation.forEach(unit => {
                                        newSelect.innerHTML += `<option value="${unit.id}">${unit.display_name}</option>`;
                                    });
                                    popContainer.appendChild(newSelect);
                                    newSelect.addEventListener('change', updatePopulationDropdowns);
                            }
                        }
                    });
                }
                
            } else if (actionKey === "buy_resources" || actionKey === "buy_goods") {
                // Generic handler for "Buy Resources", "Buy Goods"
                let formHTML = '';
                if (actionKey === "buy_resources") {
                    formHTML = `
                        <label for="resource_id_buy">Resource Type:</label>
                        <select id="resource_id_buy" name="resource_id" required></select><br><br>
                        <label for="quantity_buy">Quantity:</label>
                        <input type="number" id="quantity_buy" name="quantity" value="1" min="1" required><br><br>
                        <p id="buy-resources-cost-preview-internal"></p>`;
                } else { // buy_goods
                    formHTML = `
                        <label for="goods_type_id_buy">Trade Good Type:</label>
                        <select id="goods_type_id_buy" name="goods_type_id" required></select><br><br>
                        <label for="quantity_buy">Quantity:</label>
                        <input type="number" id="quantity_buy" name="quantity" value="1" min="1" required><br><br>
                        <p id="buy-goods-cost-preview-internal"></p>`;
                }
                dynamicInputsDiv.innerHTML = formHTML;
                
                if (actionKey === "buy_resources") {
                    const resourceSelect = document.getElementById('resource_id_buy');
                    const quantityInput = document.getElementById('quantity_buy');
                    const previewP = document.getElementById('buy-resources-cost-preview-internal');
                    await fetchSelectOptions(resourceTypesUrl, resourceSelect);
                    const updatePreview = () => updateBuyResourcesPreview(resourceSelect, quantityInput, previewP);
                    resourceSelect.onchange = updatePreview;
                    quantityInput.oninput = updatePreview;
                    updatePreview();
                } else { // buy_goods
                    const goodsSelect = document.getElementById('goods_type_id_buy');
                    const quantityInput = document.getElementById('quantity_buy');
                    const previewP = document.getElementById('buy-goods-cost-preview-internal');
                    await fetchSelectOptions(goodsTypesUrl, goodsSelect);
                    const updatePreview = () => updateBuyGoodsPreview(goodsSelect, quantityInput, previewP);
                    goodsSelect.onchange = updatePreview;
                    quantityInput.oninput = updatePreview;
                    updatePreview();
                }
            } else {
                // Generic handler for actions like "Recruit Population"
                await buildGenericInputs(action, dynamicInputsDiv);
            }
            
            unifiedActionModal.style.display = 'flex';
        });
    });
    
    // --- Modal Close & Other Listeners ---
    closeButton.addEventListener('click', () => { unifiedActionModal.style.display = 'none'; });
    window.addEventListener('click', (event) => { if (event.target === unifiedActionModal) unifiedActionModal.style.display = 'none'; });
    actionDetailsLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const actionName = this.getAttribute('data-action');
            const action = actionsMap.get(actionName);
            if (action) {
                modalTitle.textContent = action.name + " (Details)";
                modalDescription.textContent = action.description + " Duration: " + action.duration + " season(s).";
                dynamicInputsDiv.innerHTML = '';
                formSubmitButton.style.display = 'none';
                unifiedActionModal.style.display = 'flex';
            }
        });
    });
    endSeasonBtn.addEventListener('click', () => { if (confirm("Are you sure you want to end the current season?")) { window.location.href = `/realm/${realmName}/end_turn/`; } });

    // --- Specific Preview Functions for Buy actions ---
    function updateBuyResourcesPreview(resourceSelect, quantityInput, previewElement) {
        const selectedResourceId = resourceSelect.value;
        const quantity = parseInt(quantityInput.value);
        if (!selectedResourceId || isNaN(quantity) || quantity <= 0) {
            previewElement.textContent = ""; formSubmitButton.disabled = true; return;
        }
        const resource = allResourcesData.find(r => r.id == selectedResourceId);
        if (!resource) { formSubmitButton.disabled = true; return; }
        const costPerUnit = resource.value_numeric;
        if (isNaN(costPerUnit)) { previewElement.textContent = "Error calculating cost."; formSubmitButton.disabled = true; return; }
        let totalCost = Math.round(costPerUnit * quantity);
        previewElement.textContent = `Total Cost: ${totalCost.toLocaleString()} Gold`;
        if (totalCost > currentTreasury) {
            const maxAffordable = Math.floor(currentTreasury / costPerUnit);
            previewElement.textContent += ` (Not enough Gold! Max: ${maxAffordable.toLocaleString()})`;
            formSubmitButton.disabled = true;
        } else {
            formSubmitButton.disabled = false;
        }
    }
    function updateBuyGoodsPreview(goodsTypeSelect, quantityInput, previewElement) {
        const selectedGoodsTypeId = goodsTypeSelect.value;
        const quantity = parseInt(quantityInput.value);
        if (!selectedGoodsTypeId || isNaN(quantity) || quantity <= 0) {
            previewElement.textContent = ""; formSubmitButton.disabled = true; return;
        }
        const goodsType = allGoodsTypesData.find(r => r.id == selectedGoodsTypeId);
        if (!goodsType) { formSubmitButton.disabled = true; return; }
        const costPerUnit = goodsType.value_numeric;
        if (isNaN(costPerUnit)) { previewElement.textContent = "Error calculating cost."; formSubmitButton.disabled = true; return; }
        let totalCost = Math.round(costPerUnit * quantity);
        previewElement.textContent = `Total Cost: ${totalCost.toLocaleString()} Gold`;
        if (totalCost > currentTreasury) {
            const maxAffordable = Math.floor(currentTreasury / costPerUnit);
            previewElement.textContent += ` (Not enough Gold! Max: ${maxAffordable.toLocaleString()})`;
            formSubmitButton.disabled = true;
        } else {
            formSubmitButton.disabled = false;
        }
    }
});