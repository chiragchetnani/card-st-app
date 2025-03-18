import streamlit as st
import pickle
import os
import bcrypt
import requests
import io
from PIL import Image
import pandas as pd

# Database files
USER_DB = "user_data.pkl"

BUSINESS_CARDS_FILE = "business_cards.pkl"
IMAGE_DIR = "business_card_images"


# Create directory if it doesn't exist
os.makedirs(IMAGE_DIR, exist_ok=True)
# Load or Initialize User Database
@st.cache_data
def load_users():
    try:
        if os.path.exists(USER_DB):
            with open(USER_DB, "rb") as f:
                return pickle.load(f)
        return {}
    except Exception as e:
        st.error(f"❌ Error loading user data: {e}")
        return {}

def save_users(users):
    try:
        pickle.dump(users, open(USER_DB, "wb"))
    except Exception as e:
        st.error(f"❌ Error saving user data: {e}")

# Load or Initialize Dropdown Data
# Load or Initialize Dropdown Data
@st.cache_data
def load_dropdowns():
    try:
        return {
            "customer_types": ["videolytical", "Endeavour", "Aasvaa", "Times Watch", "others"]
        }
    except Exception as e:
        st.error(f"❌ Error loading dropdown data: {e}")
        return {}



# Load existing business cards
def load_business_cards():
    if os.path.exists(BUSINESS_CARDS_FILE):
        with open(BUSINESS_CARDS_FILE, "rb") as f:
            return pickle.load(f)
    return []  # Return an empty list if no data exists

# Save business cards
def save_business_cards(data):
    try:
        with open(BUSINESS_CARDS_FILE, "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        st.error(f"❌ Error saving business cards: {e}")

# Initialize the business cards list
business_cards = load_business_cards()

# Simulate auto-incrementing ID
if business_cards:
    next_id = max(card["id"] for card in business_cards) + 1
else:
    next_id = 1

# Function to add a new business card
def add_business_card(username, company_name, card_holder, designation, mobile_number, email, website, address, customer_type,remarks, image_path):
    global next_id
    new_card = {
        "id": next_id,
        "username": username,  # Associate card with the user
        "company_name": company_name,
        "card_holder": card_holder,
        "designation": designation,
        "mobile_number": mobile_number,
        "email": email,
        "website": website,
        "address": address,
        "customer_type": customer_type,
        
        "remarks": remarks,
        "image_path": image_path
    }
    business_cards.append(new_card)
    save_business_cards(business_cards)
    next_id += 1
    return new_card

# Function to get all saved business cards
def get_all_business_cards():
    return load_business_cards()

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this to a more secure password in production

# Register a new user
def register_user(username, password):
    users = load_users()
    if username in users:
        return False  
    users[username] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    save_users(users)
    return True

# Authenticate user login
def login_user(username, password):
    users = load_users()
    # Check for hardcoded admin credentials
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.is_admin = True  # Admin privileges
        return True
    # Check for regular user credentials
    elif username in users and bcrypt.checkpw(password.encode(), users[username].encode()):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.is_admin = False  # Regular user
        return True
    return False

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.is_admin = False

st.title("📇 Business Card Recognition")

# **Authentication**
if not st.session_state.logged_in:
    st.sidebar.subheader("🔑 Login / Signup")
    auth_option = st.sidebar.radio("Choose an option", ("Login", "Register"))
    username = st.sidebar.text_input("👤 Username")
    password = st.sidebar.text_input("🔒 Password", type="password")

    if auth_option == "Register" and st.sidebar.button("📝 Register"):
        if register_user(username, password):
            st.sidebar.success("✅ Registration successful!")
        else:
            st.sidebar.error("🚫 Username already exists!")

    if auth_option == "Login" and st.sidebar.button("🔑 Login"):
        if login_user(username, password):
            st.sidebar.success(f"✅ Welcome, {username}!")
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.sidebar.error("❌ Invalid username or password.")
    st.stop()

# **Main App (After Login)**
st.sidebar.success(f"Welcome, {st.session_state.username} 👋")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.is_admin = False
    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()


# **Delete Data Section**
st.sidebar.header("🗑️ Delete Data")

# Dropdown to select which data to delete
data_to_delete = st.sidebar.selectbox("Select data to delete:", 
                                       ["None", "User  Data", "Business Cards"])

if st.sidebar.button("Delete Selected Data"):
    if data_to_delete == "User  Data":
        if os.path.exists(USER_DB):
            os.remove(USER_DB)
            st.success("✅ User data has been deleted successfully!")
        else:
            st.warning("⚠️ User data file does not exist.")
    
    elif data_to_delete == "Business Cards":
        if os.path.exists(BUSINESS_CARDS_FILE):
            os.remove(BUSINESS_CARDS_FILE)
            st.success("✅ Business cards have been deleted successfully!")
        else:
            st.warning("⚠️ Business cards file does not exist.")
    else:
        st.warning("⚠️ No data selected for deletion.")
# Load dropdown data
dropdowns = load_dropdowns()
customer_types = dropdowns["customer_types"]

# **Business Card Operations**
option = st.radio("Select Image Source:", ("Upload", "View Saved Cards", "Capture"))

if option == "Capture":
    st.header("📷 Capture Image from Webcam")
    img_file = st.camera_input("Take a picture")

    if img_file:
        img = Image.open(img_file)
        img = img.resize((800, 800))  # Resize image to reduce processing time
        st.image(img, caption="📷 Captured Image", use_column_width=True)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        with st.spinner("⏳ Extracting details..."):
            try:
                response = requests.post("http://34.60.231.140/:8000/upload/", files={"file": img_byte_arr})
                response.raise_for_status()
                extracted_data = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to FastAPI: {e}")
                st.stop()

        if extracted_data:
            st.success("✅ Extraction successful! Edit details below:")
            company_name = st.text_input("🏢 Company Name", extracted_data.get("business_name", ""))
            card_holder = st.text_input("🙍 Card Holder Name", extracted_data.get("name_of_card_holder", ""))
            designation = st.text_input("💼 Designation", extracted_data.get("designation", ""))
            mobile_number = st.text_input("📞 Mobile Number", extracted_data.get("contact_no", ""))
            email = st.text_input("✉️ Email", extracted_data.get("email", ""))
            website = st.text_input("🌐 Website", extracted_data.get("website", ""))
            address = st.text_area("📍 Address", extracted_data.get("address", ""))
            remarks = st.text_area("📝 Remarks", "")

            # Use the loaded customer types for the dropdown
            customer_type = st.selectbox("👤 Customer Type", customer_types)


            if st.button("💾 Save"):
                image_path = os.path.join(IMAGE_DIR, f"card_{next_id}.png")
                img.save(image_path)  # Save the captured image
                add_business_card(st.session_state.username, company_name, card_holder, designation, mobile_number, email, website, address, customer_type, remarks, image_path)
                st.success("✅ Card saved successfully!")

if option == "Upload":
    image = st.file_uploader("📤 Upload Image", type=["png", "jpg", "jpeg"])
    if image:
        img = Image.open(image)
        img = img.resize((800, 800))  # Resize image to reduce processing time
        st.image(img, caption="📷 Uploaded Image", use_column_width=True)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        with st.spinner("⏳ Extracting details..."):
            try:
                response = requests.post("http://127.0.0.1:8000/upload/", files={"file": img_byte_arr})
                response.raise_for_status()
                extracted_data = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to FastAPI: {e}")
                st.stop()

        if extracted_data:
            st.success("✅ Extraction successful! Edit details below:")
            company_name = st.text_input("🏢 Company Name", extracted_data.get("business_name", ""))
            card_holder = st.text_input("🙍 Card Holder Name", extracted_data.get("name_of_card_holder", ""))
            designation = st.text_input("💼 Designation", extracted_data.get("designation", ""))
            mobile_number = st.text_input("📞 Mobile Number", extracted_data.get("contact_no", ""))
            email = st.text_input("✉️ Email", extracted_data.get("email", ""))
            website = st.text_input("🌐 Website", extracted_data.get("website", ""))
            address = st.text_area("📍 Address", extracted_data.get("address", ""))
            remarks = st.text_area("📝 Remarks", "")

            # Use the updated names for dropdowns
            # Use the loaded customer types for the dropdown
            customer_type = st.selectbox("👤 Customer Type", customer_types)


            st.write("Selected Customer Type:", customer_type)
            
            if st.button("💾 Save"):
                image_path = os.path.join(IMAGE_DIR, f"card_{next_id}.png")
                img.save(image_path)  # Save the uploaded image
                add_business_card(st.session_state.username, company_name, card_holder, designation, mobile_number, email, website, address, customer_type,  remarks, image_path)
                st.success("✅ Card saved successfully!")

if option == "View Saved Cards":
    saved_cards = get_all_business_cards()
    if saved_cards:
        st.write("📁 Your Saved Business Cards" if not st.session_state.is_admin else "📁 All Saved Business Cards")
        try:
            # Filter cards based on user role
            if st.session_state.is_admin:
                df = pd.json_normalize(saved_cards)  # Admin can see all cards
            else:
                # Regular user sees only their cards
                user_cards = [card for card in saved_cards if "username" in card and card["username"] == st.session_state.username]
                df = pd.json_normalize(user_cards)

            if df.empty:
                st.warning("⚠️ No saved business cards found for your account.")
            else:
                st.dataframe(df)  # Display as a table
                
                # Add download button for Excel
                excel_file = io.BytesIO()
                with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Business Cards')
                excel_file.seek(0)  # Move to the beginning of the BytesIO buffer

                st.download_button(
                    label="📥 Download Saved Cards as Excel",
                    data=excel_file,
                    file_name="business_cards.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Display saved images
                for card in saved_cards:
                    if st.session_state.is_admin or (card.get("username") == st.session_state.username):  # Check if the user is admin or the owner of the card
                        image_path = card.get("image_path")  # Use .get() to avoid KeyError
                        if image_path and os.path.exists(image_path):  # Check if the image file exists
                            st.image(image_path, caption=f"Card ID: {card['id']}", use_column_width=True)
                        else:
                            st.warning(f"⚠️ No image found for Card ID: {card['id']}")
        except Exception as e:
            st.error(f"❌ Error displaying saved cards: {e}")
            st.write("Debug Info: ", saved_cards)  # Output the saved cards ```python
    else:
        st.warning("⚠️ No saved business cards found.")
