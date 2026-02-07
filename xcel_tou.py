import streamlit as st
from xcel_pdf import extract_usage_from_pdf, open_pdf, plan_cost, is_bill_winter

st.title("Xcel Energy Rate Comparison")

st.header("Time of Use Rates (TOU)")
tou_off_winter, tou_on_winter, tou_off_summer, tou_on_summer = st.columns(4)
with tou_off_winter:
    plan_tou_off_winter = st.number_input("Off-Peak Winter Rate ($/kWh)", value=0.06792, key="tou_off_winter", format="%.5f")
with tou_on_winter:
    plan_tou_on_winter = st.number_input("On-Peak Winter Rate ($/kWh)", value=0.18331, key="tou_on_winter", format="%.5f")
with tou_off_summer:
    plan_tou_off_summer = st.number_input("Off-Peak Summer Rate ($/kWh)", value=0.07884, key="tou_off_summer", format="%.5f")
with tou_on_summer:
    plan_tou_on_summer = st.number_input("On-Peak Summer Rate ($/kWh)", value=0.21277, key="tou_on_summer", format="%.5f")

st.header("Flat Rates")
flat_winter, flat_summer = st.columns(2)
with flat_winter:
    plan_flat_winter = st.number_input("Flat Rate Winter ($/kWh)", value=0.08570, key="flat_winter", format="%.5f")
with flat_summer:
    plan_flat_summer = st.number_input("Flat Rate Summer ($/kWh)", value=0.10380, key="flat_summer", format="%.5f")

uploaded_files = st.file_uploader("Upload Xcel PDF Bills", type="pdf", accept_multiple_files=True)

if uploaded_files:
    total_cost_tou = 0
    total_cost_flat = 0
    aggregated_usage = {}
    
    individual_results = []

    for uploaded_file in uploaded_files:
        try:
            pdf = open_pdf(uploaded_file)
            usage = extract_usage_from_pdf(pdf)
            is_winter = is_bill_winter(pdf)
            
            # Default to winter if unable to determine, or handle specifically
            season = "Winter" if is_winter is not False else "Summer"
            
            if season == "Winter":
                rate_tou = {
                    "Off-PeakEnergy": plan_tou_off_winter,
                    "On-PeakEnergy": plan_tou_on_winter
                }
                rate_flat = {
                    "Off-PeakEnergy": plan_flat_winter,
                    "On-PeakEnergy": plan_flat_winter
                }
            else:
                rate_tou = {
                    "Off-PeakEnergy": plan_tou_off_summer,
                    "On-PeakEnergy": plan_tou_on_summer
                }
                rate_flat = {
                    "Off-PeakEnergy": plan_flat_summer,
                    "On-PeakEnergy": plan_flat_summer
                }

            cost_tou = plan_cost(usage, rate_tou)
            cost_flat = plan_cost(usage, rate_flat)

            total_cost_tou += cost_tou
            total_cost_flat += cost_flat
            
            for k, v in usage.items():
                aggregated_usage[k] = aggregated_usage.get(k, 0) + v
            
            individual_results.append({
                "File": uploaded_file.name,
                "Season": season,
                "TOU Cost": f"${cost_tou:.2f}",
                "Flat Cost": f"${cost_flat:.2f}",
                "Total kWh": sum(usage.values())
            })
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")

    if individual_results:
        st.subheader("Aggregated Cost Comparison")
        col1, col2 = st.columns(2)
        col1.metric("Total TOU Cost", f"${total_cost_tou:.2f}")
        col2.metric("Total Flat Cost", f"${total_cost_flat:.2f}")

        if total_cost_tou < total_cost_flat:
            st.success(f"Time of Use Plan is cheaper by ${total_cost_flat - total_cost_tou:.2f} overall")
        elif total_cost_flat < total_cost_tou:
            st.success(f"Flat Plan is cheaper by ${total_cost_tou - total_cost_flat:.2f} overall")
        else:
            st.info("Both plans cost the same overall.")

        st.subheader("Aggregated Usage")
        st.json(aggregated_usage)

        with st.expander("View Individual Bill Details"):
            st.table(individual_results)
