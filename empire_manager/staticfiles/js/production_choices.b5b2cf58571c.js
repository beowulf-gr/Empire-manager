document.addEventListener("DOMContentLoaded", function() {
    const unitTypeSelect = document.getElementById("id_unit_type");

    // Function to handle the unit type selection change event
    unitTypeSelect.addEventListener("change", function() {
        const unitTypeId = unitTypeSelect.value;
        console.log("Unit type changed to:", unitTypeId);  // Debugging log

        // Check if production choices already exist
        let productionChoiceSelect = document.getElementById("id_production_choice");
        
        // If no production choice dropdown exists, create it
        if (!productionChoiceSelect) {
            productionChoiceSelect = createProductionChoiceDropdown();
        }

        // Show the production choice dropdown
        const productionChoiceField = document.getElementById("production-choice-field");
        productionChoiceField.style.display = "block"; // Make sure it's visible

        // Clear existing options in the production choice dropdown
        productionChoiceSelect.innerHTML = '<option value="">Select a Production Option</option>';

        // If a valid unit type is selected, fetch the production choices
        if (unitTypeId) {
            fetch(`/realm/get-production-choices/?unit_type_id=${unitTypeId}`)
                .then(response => response.json())
                .then(data => {
                    // If there are valid choices, populate the dropdown
                    if (data.choices && data.choices.length > 0) {
                        data.choices.forEach(choice => {
                            const option = document.createElement("option");
                            option.value = choice[0];
                            option.textContent = choice[1];
                            productionChoiceSelect.appendChild(option);
                        });
                    } else {
                        productionChoiceField.style.display = 'none'; // Keep hidden if no choices
                        console.log("No production choices available for this unit type");
                    }
                })
                .catch(error => {
                    console.error('Error fetching production choices:', error);
                });
        } else {
            // Hide the dropdown if no valid unit type is selected
            productionChoiceField.style.display = "none";
        }
    });

    // Function to create the production choice dropdown dynamically
    function createProductionChoiceDropdown() {
        // Create a div container for the new dropdown
        const productionChoiceField = document.createElement("div");
        productionChoiceField.id = "production-choice-field";
        
        // Create the select dropdown for production choices
        const productionChoiceSelect = document.createElement("select");
        productionChoiceSelect.id = "id_production_choice";
        productionChoiceSelect.name = "production_choice";
        productionChoiceSelect.innerHTML = '<option value="">Select a Production Option</option>';

        // Append the production choice dropdown to the page (or specific container)
        document.querySelector("#form-container").appendChild(productionChoiceField);
        productionChoiceField.appendChild(productionChoiceSelect);

        return productionChoiceSelect;
    }
});
