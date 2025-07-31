// Use a DOMContentLoaded listener to ensure all HTML is loaded before the script runs
document.addEventListener('DOMContentLoaded', () => {
    const gameData = document.getElementById('game-data').dataset;
    const realmName = gameData.realmName;
    const csrfToken = gameData.csrfToken;
    const previewUrl = gameData.previewUrl;
    const idlePopUrl = gameData.idlePopUrl;
    const landUnitsUrl = gameData.landUnitsUrl;
    const strongholdSelect = gameData.strongholdTypesUrl;
    const roadEligibleUrl = gameData.roadEligibleUrl;
    const mineEligibleUrl = gameData.mineEligibleUrl;

    const currentTreasury = parseFloat(document.getElementById('realm-info').dataset.treasury);

    // --- Global DOM element references (define once) ---
    const actionButtons = document.querySelectorAll('.action-button');
    const actionDetailsLinks = document.querySelectorAll('.action-details-link');
    const unifiedActionModal = document.getElementById('unified-action-modal');
    const closeButton = unifiedActionModal.querySelector('.close-button');
    const modalTitle = document.getElementById('modal-title');
    const modalDescription = document.getElementById('modal-description');
    const dynamicActionForm = document.getElementById('dynamic-action-form');
    const formActionType = document.getElementById('form-action-type');
    const formDuration = document.getElementById('form-duration');
    const dynamicInputsDiv = document.getElementById('dynamic-inputs');
    const formSubmitButton = document.getElementById('form-submit-button');
    const endSeasonBtn = document.getElementById('end-season-btn');
    const availableActionsData = JSON.parse(document.getElementById('available-actions-data').textContent);

    let allIdlePopulation = []; // Global store for available population units

    // Preview elements (always exist, hidden/shown as needed)
    const buyResourcesCostPreview = document.getElementById('buy-resources-cost-preview'); // For Buy Resources
    const buyGoodsCostPreview = document.getElementById('buy-goods-cost-preview'); // For Buy Resources

    // Map to quickly find action details by slug or name
    const actionsMap = new Map();
    availableActionsData.forEach(action => {
        actionsMap.set(action.name, action);
        actionsMap.set(action.action_key, action); // <-- Change to 'action_key'
    });

    // Store fetched data for client-side calculations
    let allGoodsTypesData = []; // Populated by get_goods_types_json
    let allResourcesData = []; // Populated by get_resource_types_json
    let allPopulationRacesData = []; // Populated by get_population_races_json

    // Helper function to fetch options for a select dropdown
    async function fetchSelectOptions(url, selectElement) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            selectElement.innerHTML = '<option value="" disabled selected>Select an option</option>';
            data.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.id;
                opt.textContent = option.name;
                // Store relevant data directly in the array that will be filtered
                if (url.includes('get_resource_types_json')) {
                    // Ensure 'value' is a number for calculation
                    option.value_numeric = parseFloat(option.value); // Convert to float if not already
                    allResourcesData.push(option);
                } else if (url.includes('get_goods_types_json')) {
                    // Ensure 'value' is a number for calculation
                    option.value_numeric = parseFloat(option.value); // Convert to float if not already
                    allGoodsTypesData.push(option);
                } else if (url.includes('get_population_races_json')) {
                    allPopulationRacesData.push(option);
                }
                selectElement.appendChild(opt);
            });
            return data; // Return data for chaining or storing
        } catch (error) {
            console.error("Error fetching options from " + url + ":", error);
            selectElement.innerHTML = '<option value="" disabled selected>Error loading options</option>';
            return []; // Return empty array on error
        }
    }

    // ### NEW: Function to update population dropdowns to be exclusive ###
    function updatePopulationDropdowns() {
        const popSelects = document.querySelectorAll('.population-select');
        const selectedValues = new Set();

        // First, find all values that are currently selected in any dropdown
        popSelects.forEach(select => {
            if (select.value) {
                selectedValues.add(select.value);
            }
        });

        // Now, update the options in every dropdown
        popSelects.forEach(select => {
            const currentSelection = select.value;
            for (const option of select.options) {
                // Show the option if it's not selected elsewhere, OR if it's the one currently selected in THIS dropdown
                if (!selectedValues.has(option.value) || option.value === currentSelection) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            }
        });
    }

    function updateLandUnitDropdowns() {
        const landUnitSelects = document.querySelectorAll('.road-land-unit-select');
        const selectedValues = new Set();

        // Find all currently selected land unit values
        landUnitSelects.forEach(select => {
            if (select.value) {
                selectedValues.add(select.value);
            }
        });

        // Loop through each dropdown and hide/show options
        landUnitSelects.forEach(select => {
            const currentSelection = select.value;
            for (const option of select.options) {
                if (!option.value) continue; // Skip the placeholder option
                // Show the option if it's not selected elsewhere, OR if it's the current selection in THIS dropdown
                if (!selectedValues.has(option.value) || option.value === currentSelection) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            }
        });
    }

    function displayCostPreview(costs) {
        const previewContainer = document.getElementById('cost-preview-container');
        if (!previewContainer) return;

        let html = '<h4>Total Cost:</h4><ul>';
        for (const [key, value] of Object.entries(costs)) {
            if (value > 0) {
                html += `<li>${key}: ${value}</li>`;
            }
        }
        html += '</ul>';
        previewContainer.innerHTML = html;
    }


    // Helper function to build dynamic input fields for a generic action
    async function buildDynamicInputs(action, containerDiv) {
        containerDiv.innerHTML = ''; // Clear existing inputs
        for (const inputDef of action.inputs) {
            const label = document.createElement('label');
            label.setAttribute('for', inputDef.name);
            label.textContent = inputDef.label;
            containerDiv.appendChild(label);

            let inputElement;
            if (inputDef.type === 'select') {
                inputElement = document.createElement('select');
                inputElement.id = inputDef.name;
                inputElement.name = inputDef.name;
                if (inputDef.required) inputElement.required = true;
                // Dynamically fetch options based on options_url (for select types)

                let url = inputDef.options_url;
                if (url.includes('placeholder')) {
                    // Dynamically insert the current realm's name into the URL
                    url = url.replace('placeholder', realmName); // Replace the placeholder
        }
                await fetchSelectOptions(url, inputElement);
            } else if (inputDef.type === 'number') {
                inputElement = document.createElement('input');
                inputElement.type = 'number';
                inputElement.id = inputDef.name;
                inputElement.name = inputDef.name;
                if (inputDef.required) inputElement.required = true;
                if (inputDef.default !== undefined) inputElement.value = inputDef.default;
                if (inputDef.min !== undefined) inputElement.min = inputDef.min;
                if (inputDef.max !== undefined) inputElement.max = inputDef.max;
            } else { // Default to text
                inputElement = document.createElement('input');
                inputElement.type = 'text';
                inputElement.id = inputDef.name;
                inputElement.name = inputDef.name;
                if (inputDef.required) inputElement.required = true;
                if (inputDef.default !== undefined) inputElement.value = inputDef.default;
            }
            containerDiv.appendChild(inputElement);
            containerDiv.appendChild(document.createElement('br'));
            containerDiv.appendChild(document.createElement('br'));
        }
    }


    // Main event listener for action buttons
    actionButtons.forEach(button => {
        button.addEventListener('click', async function(event) {
            const actionKey = this.getAttribute('data-action-slug');
            const action = actionsMap.get(actionKey);

            if (!action) {
                console.error("Action details not found for:", actionKey);
                return;
            }

            // Reset modal for new action
            modalTitle.textContent = action.name;
            modalDescription.textContent = action.description;
            formActionType.value = action.action_key; // Use display name for submission
            formDuration.value = action.duration;
            formSubmitButton.textContent = action.submit_text;
            dynamicInputsDiv.innerHTML = ''; // Clear previous inputs
            formSubmitButton.style.display = 'block'; // Ensure submit button is visible

            

            // Fetch all idle population units once and store them
            const idlePopRes = await fetch(`/realm/${realmName}/get_idle_population_json/`);
            allIdlePopulation = await idlePopRes.json();

            // Hide all preview elements by default, specific logic will show them
            buyResourcesCostPreview.style.display = 'none'; // For Buy Resources
            buyGoodsCostPreview.style.display = 'none'; // For Buy Goods

            if (action.inputs && action.inputs.length > 0) {
                await buildDynamicInputs(action, dynamicInputsDiv);
            }
            
            if (actionKey === 'construct_stronghold') {
            // 1. Create the initial, static dropdowns
            dynamicInputsDiv.innerHTML = `
                <label for="stronghold_type">Stronghold Type:</label>
                <select id="stronghold_type" name="stronghold_type" required></select>
                <br><br>
                <label for="land_unit">Location (Land Unit):</label>
                <select id="land_unit" name="land_unit" required></select>
                <br><br>
                <label for="stronghold_name">Stronghold Name (Optional):</label>
                <input type="text" id="stronghold_name" name="stronghold_name">
                <br><br>
                <div id="population-dropdown-container"></div>
            `;

            // 2. Get references to the new elements
            const strongholdSelect = document.getElementById('stronghold_type');
            const landUnitSelect = document.getElementById('land_unit');
            const popContainer = document.getElementById('population-dropdown-container');

            // 3. Populate the static dropdowns
            await fetchSelectOptions("{% url 'get_stronghold_types_json' %}", strongholdSelect);
            await fetchSelectOptions("{% url 'get_land_units_json' realm_name=realm.name %}", landUnitSelect);

            // Fetch all idle population units once and store them
            const idlePopRes = await fetch(`/realm/${realmName}/get_idle_population_json/`);
            allIdlePopulation = await idlePopRes.json();

            // 4. Add an event listener to the stronghold dropdown
            strongholdSelect.addEventListener('change', async function() {
                const strongholdId = this.value;
                popContainer.innerHTML = ''; // Clear previous dropdowns
                if (!strongholdId) return;
                
                const strongholdDetailsRes = await fetch(`/realm/get_stronghold_type_details_json/${strongholdId}/`);
                const strongholdDetails = await strongholdDetailsRes.json();
                const requiredPop = strongholdDetails.population_cost;

                if (allIdlePopulation.length < requiredPop) {
                    popContainer.innerHTML = `<p style="color: red;">Not enough idle population! Requires ${requiredPop}, but only ${allIdlePopulation.length} available.</p>`;
                    formSubmitButton.disabled = true;
                    return;
                }

                formSubmitButton.disabled = false;
                popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;

                // 5. Create a dropdown for each required population unit
                for (let i = 0; i < requiredPop; i++) {
                    const newLabel = document.createElement('label');
                    newLabel.textContent = `Unit #${i + 1}:`;
                    
                    const newSelect = document.createElement('select');
                    newSelect.name = 'assigned_population'; // Same name for all
                    newSelect.className = 'population-select'; // Class for easy selection
                    newSelect.required = true;
                    
                    // Add a default, empty option
                    newSelect.innerHTML = '<option value="" selected>-- Select a Unit --</option>';

                    // Populate with all available idle units
                    allIdlePopulation.forEach(unit => {
                        newSelect.innerHTML += `<option value="${unit.id}">${unit.display_name}</option>`;
                    });

                    // Add the new dropdown to the page
                    popContainer.appendChild(newLabel);
                    popContainer.appendChild(newSelect);
                    popContainer.appendChild(document.createElement('br'));

                    // Add the event listener to update other dropdowns on change
                    newSelect.addEventListener('change', updatePopulationDropdowns);
                }
            });

                } else if (actionKey === 'build_roads') {
                // ### NEW LOGIC FOR BUILD ROADS ###
                dynamicInputsDiv.innerHTML = `
                    <p>Select up to 4 land units (at least 1 is required):</p>
                    <div id="land-unit-dropdowns"></div>
                    <div id="population-dropdown-container"></div>
                `;
                
                const landUnitContainer = document.getElementById('land-unit-dropdowns');
                const popContainer = document.getElementById('population-dropdown-container');
                
                // Fetch and build the checklist of land units
                const landUnitsRes = await fetch(`{% url 'get_road_eligible_land_units_json' realm_name=realm.name %}`);
                const landUnits = await landUnitsRes.json();
                
                // Create 4 dropdowns for land units
                for (let i = 0; i < 4; i++) {
                    const select = document.createElement('select');
                    select.name = 'land_units_for_roads';
                    select.className = 'road-land-unit-select';
                    select.innerHTML = `<option value="">-- Optional Unit #${i + 1} --</option>`;
                    if (i === 0) {
                        select.required = true; // First one is compulsory
                        select.innerHTML = '<option value="" disabled selected>-- Select Required Unit #1 --</option>';
                    }
                    landUnits.forEach(unit => {
                        select.innerHTML += `<option value="${unit.id}" data-has-stronghold="${unit.has_stronghold}">${unit.name}</option>`;
                    });
                    landUnitContainer.appendChild(select);

                    select.addEventListener('change', updateLandUnitDropdowns);
                }

                // Function to recalculate and render population dropdowns
                // const recalculatePopulation = () => {
                //     const selectedOptions = document.querySelectorAll('.road-land-unit-select option:checked');
                    
                //     let requiredPop = 1;
                //     selectedOptions.forEach(option => {
                //         if (option.value && option.dataset.hasStronghold === 'false') {
                //             requiredPop += 1;
                //         }
                //     });

                const recalculatePopulation = async () => { // Make this function async
                    const selectedOptions = document.querySelectorAll('.road-land-unit-select option:checked');
                    let selected_land_ids = [];
                    selectedOptions.forEach(opt => {
                        if (opt.value) selected_land_ids.push(opt.value);
                    });

                    const response = await fetch(`{% url 'preview_action_cost' realm_name=realm.name %}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        body: JSON.stringify({
                            action_key: 'build_roads',
                            land_unit_ids: selected_land_ids
                        })
                    });
                    const costs = await response.json();
                
                    // Display the cost received from the server
                    displayCostPreview(costs);

                        // Update population dropdowns based on the cost from the server
                    const requiredPop = costs.population || 0;

                    popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;
                    if (allIdlePopulation.length < requiredPop) {
                        popContainer.innerHTML += `<p style="color: red;">Not enough idle population!</p>`;
                        formSubmitButton.disabled = true;
                    } else {
                        formSubmitButton.disabled = false;
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
                };

                // Add event listener to the container to catch changes from ANY select
                landUnitContainer.addEventListener('change', recalculatePopulation);

                // Trigger the calculation once to set the initial state
                recalculatePopulation();

            } else if (actionKey === 'build_mine') {
                // ### NEW LOGIC FOR BUILD MINE ###
                const requiredPop = 1; // Static cost
                dynamicInputsDiv.innerHTML = `
                    <label for="land_unit_for_mine">Select Land Unit:</label>
                    <select id="land_unit_for_mine" name="land_unit_for_mine" required></select>
                    <br><br>
                    <div id="population-dropdown-container"></div>
                `;
                
                const landUnitSelect = document.getElementById('land_unit_for_mine');
                const popContainer = document.getElementById('population-dropdown-container');
                await fetchSelectOptions(`{% url 'get_mine_eligible_land_units_json' realm_name=realm.name %}`, landUnitSelect);

                // Build the population dropdown
                popContainer.innerHTML = `<p>Assign ${requiredPop} population unit(s):</p>`;
                if (allIdlePopulation.length < requiredPop) {
                popContainer.innerHTML += `<p style="color: red;">Not enough idle population!</p>`;
                formSubmitButton.disabled = true;
                } else {
                formSubmitButton.disabled = false;
                const newSelect = document.createElement('select');
                newSelect.name = 'assigned_population';
                newSelect.className = 'population-select'; // Use class for consistency
                newSelect.required = true;
                newSelect.innerHTML = '<option value="" selected>-- Select a Unit --</option>';
                allIdlePopulation.forEach(unit => {
                    newSelect.innerHTML += `<option value="${unit.id}">${unit.display_name}</option>`;
                });
                popContainer.appendChild(newSelect);
                // No need to call updatePopulationDropdowns since there's only one
                }

            } else if (actionKey === "buy_resources") { // Handle "Buy Resources" action
                dynamicInputsDiv.innerHTML = `
                    <label for="resource_id_buy">Resource Type:</label>
                    <select id="resource_id_buy" name="resource_id" required>
                        <option value="" disabled selected>Select Resource Type</option>
                    </select><br><br>

                    <label for="quantity_buy">Quantity:</label>
                    <input type="number" id="quantity_buy" name="quantity" value="1" min="1" required><br><br>

                    <label for="knowledge_economics_modifier_buy">Knowledge (Economics) Modifier:</label>
                    <input type="number" id="knowledge_economics_modifier_buy" name="knowledge_economics_modifier" value="0" required><br><br>
                    
                    <p>Current Treasury: ${currentTreasury.toLocaleString()} Gold</p>
                    <p id="buy-resources-cost-preview-internal"></p> {# Cost preview for buy resources #}
                `;
                // Re-get references to newly created elements inside the modal
                const newResourceIdSelect = document.getElementById('resource_id_buy');
                const newQuantityInput = document.getElementById('quantity_buy');
                const newKnowledgeModifierInput = document.getElementById('knowledge_economics_modifier_buy');
                const newBuyResourcesCostPreviewInternal = document.getElementById('buy-resources-cost-preview-internal');

                await fetchSelectOptions("{% url 'get_resource_types_json' %}", newResourceIdSelect);
                
                // Add event listeners for cost preview
                newResourceIdSelect.onchange = () => updateBuyResourcesPreview(newResourceIdSelect, newQuantityInput, newBuyResourcesCostPreviewInternal);
                newQuantityInput.oninput = () => updateBuyResourcesPreview(newResourceIdSelect, newQuantityInput, newBuyResourcesCostPreviewInternal);
                newKnowledgeModifierInput.oninput = () => updateBuyResourcesPreview(newResourceIdSelect, newQuantityInput, newBuyResourcesCostPreviewInternal);
                
                // Initial update call
                updateBuyResourcesPreview(newResourceIdSelect, newQuantityInput, newBuyResourcesCostPreviewInternal);
                buyResourcesCostPreview.style.display = 'block'; // Show external buy resources preview container

            } else if (actionKey === "buy_goods") { // Handle "Buy Goods" action
                dynamicInputsDiv.innerHTML = `
                    <label for="goods_type_id_buy">Trade Good Type:</label>
                    <select id="goods_type_id_buy" name="goods_type_id" required>
                        <option value="" disabled selected>Select Trade Good Type</option>
                    </select><br><br>

                    <label for="quantity_buy">Quantity:</label>
                    <input type="number" id="quantity_buy" name="quantity" value="1" min="1" required><br><br>

                    <label for="knowledge_economics_modifier_buy">Knowledge (Economics) Modifier:</label>
                    <input type="number" id="knowledge_economics_modifier_buy" name="knowledge_economics_modifier" value="0" required><br><br>
                    
                    <p>Current Treasury: ${currentTreasury.toLocaleString()} Gold</p>
                    <p id="buy-goods-cost-preview-internal"></p> {# Cost preview for buy Goods #}
                `;
                // Re-get references to newly created elements inside the modal
                const newGoodsTypeSelect = document.getElementById('goods_type_id_buy');
                const newQuantityInput = document.getElementById('quantity_buy');
                const newKnowledgeModifierInput = document.getElementById('knowledge_economics_modifier_buy');
                const newBuyGoodsCostPreviewInternal = document.getElementById('buy-goods-cost-preview-internal');

                await fetchSelectOptions("{% url 'get_goods_types_json' %}", newGoodsTypeSelect);
                
                // Add event listeners for cost preview
                newGoodsTypeSelect.onchange = () => updateBuyGoodsPreview(newGoodsTypeSelect, newQuantityInput, newBuyGoodsCostPreviewInternal);
                newQuantityInput.oninput = () => updateBuyGoodsPreview(newGoodsTypeSelect, newQuantityInput, newBuyGoodsCostPreviewInternal);
                newKnowledgeModifierInput.oninput = () => updateBuyGoodsPreview(newGoodsTypeSelect, newQuantityInput, newBuyGoodsCostPreviewInternal);
                
                // Initial update call
                updateBuyGoodsPreview(newGoodsTypeSelect, newQuantityInput, newBuyGoodsCostPreviewInternal);
                buyGoodsCostPreview.style.display = 'block'; // Show external buy resources preview container
            }
            // else {
            //     // Generic actions with standard inputs (or no inputs)
            //     if (action.inputs && action.inputs.length > 0) {
            //         await buildDynamicInputs(action, dynamicInputsDiv);
            //     }
            // }
            unifiedActionModal.style.display = 'flex';
            formSubmitButton.style.display = 'block';
        });
    });

    // Handle clicking the "Details" link (just shows description, no form)
    actionDetailsLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const actionName = this.getAttribute('data-action');
            const action = actionsMap.get(actionName); // Get full action definition by name
            if (!action) {
                console.error("Action details not found for:", actionName);
                return;
            }
            if (action) {
                modalTitle.textContent = action.name + " (Details)";
                modalDescription.textContent = action.description + " Duration: " + action.duration + " season(s).";
                // Hide form elements if just showing details
                dynamicInputsDiv.innerHTML = '';
                formSubmitButton.style.display = 'none';
                // Hide all preview elements
                // costPreview.style.display = 'none';
                buyResourcesCostPreview.style.display = 'none';
                // tradePreview.style.display = 'none';
                unifiedActionModal.style.display = 'flex';
            }
        });
    });

    // Universal close button for the unified modal
    closeButton.addEventListener('click', function() {
        unifiedActionModal.style.display = 'none';
        formSubmitButton.style.display = 'block';
        // Hide all preview elements on close
        // costPreview.style.display = 'none';
        buyResourcesCostPreview.style.display = 'none';
        // tradePreview.style.display = 'none';
    });

    // Close modal by clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === unifiedActionModal) {
            unifiedActionModal.style.display = 'none';
            formSubmitButton.style.display = 'block';
            // Hide all preview elements on close
            // costPreview.style.display = 'none';
            buyResourcesCostPreview.style.display = 'none';
            // tradePreview.style.display = 'none';
        }
    });

    // End Season button
    endSeasonBtn.addEventListener('click', function() {
        if (confirm("Are you sure you want to end the current season?")) {
            window.location.href = "{% url 'end_turn' realm_name=realm.name %}";
        }
    });

    // NEW: Helper function for "Buy Resources" preview
    function updateBuyResourcesPreview(resourceSelect, quantityInput, previewElement) {
        const selectedResourceId = resourceSelect.value;
        const quantity = parseInt(quantityInput.value);

        previewElement.textContent = "";

        if (!selectedResourceId || isNaN(quantity) || quantity <= 0) {
            // Also disable submit button if inputs are invalid
            formSubmitButton.disabled = true;
            return;
        }

        const resource = allResourcesData.find(r => r.id == selectedResourceId);
        if (!resource) {
            formSubmitButton.disabled = true; // Disable if resource not found
            return;
        }

        // Use the correctly parsed numeric value
        const costPerUnit = resource.value_numeric; 

        // Additional check in case value_numeric didn't parse correctly
        if (isNaN(costPerUnit)) {
            console.error("Resource value_numeric is NaN for resource:", resource.name);
            previewElement.textContent = "Error calculating cost.";
            formSubmitButton.disabled = true;
            return;
        }

        let totalCost = Math.round(costPerUnit * quantity);
        
        previewElement.textContent = `Total Cost: ${totalCost.toLocaleString()} Gold`;

        // Client-side check for sufficient treasury
        if (totalCost > currentTreasury) {
            const maxAffordable = Math.floor(currentTreasury / resource.value);
            previewElement.textContent += ` (Not enough Gold! Max: ${maxAffordable.toLocaleString()})`;
            formSubmitButton.disabled = true; // Disable submit button
        } else {
            formSubmitButton.disabled = false; // Enable submit button
        }
    }

    // NEW: Helper function for "Buy Resources" preview
    function updateBuyGoodsPreview(goodsTypeSelect, quantityInput, previewElement) {
        const selectedGoodsTypeId = goodsTypeSelect.value;
        const quantity = parseInt(quantityInput.value);

        previewElement.textContent = "";

        if (!selectedGoodsTypeId || isNaN(quantity) || quantity <= 0) {
            // Also disable submit button if inputs are invalid
            formSubmitButton.disabled = true;
            return;
        }

        const goodsType = allGoodsTypesData.find(r => r.id == selectedGoodsTypeId);
        if (!goodsType) {
            formSubmitButton.disabled = true; // Disable if resource not found
            return;
        }

        // Use the correctly parsed numeric value
        const costPerUnit = goodsType.value_numeric; 

        // Additional check in case value_numeric didn't parse correctly
        if (isNaN(costPerUnit)) {
            console.error("GoodsType value_numeric is NaN for good:", goodsType.name);
            previewElement.textContent = "Error calculating cost.";
            formSubmitButton.disabled = true;
            return;
        }

        let totalCost = Math.round(costPerUnit * quantity);
        
        previewElement.textContent = `Total Cost: ${totalCost.toLocaleString()} Gold`;

        // Client-side check for sufficient treasury
        if (totalCost > currentTreasury) {
            const maxAffordable = Math.floor(currentTreasury / goodsType.value);
            previewElement.textContent += ` (Not enough Gold! Max: ${maxAffordable.toLocaleString()})`;
            formSubmitButton.disabled = true; // Disable submit button
        } else {
            formSubmitButton.disabled = false; // Enable submit button
        }
    }
});