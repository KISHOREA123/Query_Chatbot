from typing import Any, Text, Dict, List
import json
import os
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


def load_certificate_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, 'certificate_data.json')

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Create both versions (with space and underscore)
            normalized_data = {}
            for key, value in data.items():
                normalized_data[key] = value
                normalized_data[key.replace('_', ' ')] = value
            return normalized_data
    except Exception as e:
        print(f"Error loading certificate data: {str(e)}")
        return {}


CERT_DATA = load_certificate_data()


class ActionResetCertificateType(Action):
    def name(self) -> Text:
        return "action_reset_certificate_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("certificate_type", None)]


class ActionProvideCertificateInfo(Action):
    def name(self) -> Text:
        return "action_provide_certificate_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="Please specify which certificate you need information about.")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have information about {cert_type} certificates.")
            return []

        # Handle different certificate structures
        if 'definition' in cert_info:  # Standard certificates
            description = cert_info['definition']
        elif 'purpose' in cert_info:  # Some special certificates might use 'purpose'
            description = cert_info['purpose']
        else:
            description = "No description available"

        issuing_auth = cert_info.get('issuing_authority', 'N/A')

        response = (
            f"{cert_info.get('name', cert_type.title())}\n\n"
            f"{description}\n\n"
            f"\nIssuing Authority: {issuing_auth}"
        )

        # Special handling for passport types
        if cert_type.lower() in ['passport', 'passports'] and 'types_of_passport' in cert_info:
            response += "\n\nTypes Available:\n"
            for p_type, p_desc in cert_info['types_of_passport'].items():
                response += f"• {p_type.replace('_', ' ').title()}: {p_desc}\n"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideApplicationProcess(Action):
    def name(self) -> Text:
        return "action_provide_application_process"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like the application process?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have application process details for {cert_type}.")
            return []

        # Handle different process structures
        process_info = None
        if 'application_process' in cert_info:
            if isinstance(cert_info['application_process'], list):
                process_info = {'steps': cert_info['application_process']}
            else:
                process_info = cert_info['application_process']
        elif 'learner_license' in cert_info:  # Driving license special case
            process_info = cert_info['learner_license']

        if not process_info or 'steps' not in process_info:
            dispatcher.utter_message(text=f"Sorry, application process not available for {cert_type}.")
            return []

        response = f"\nApplication Process for {cert_info.get('name', cert_type.title())}:**\n\n"
        response += "\n".join([f"• {step}" for step in process_info['steps']])

        # Add processing time if available
        if 'processing_time' in process_info:
            if isinstance(process_info['processing_time'], dict):
                response += "\n\nProcessing Times:\n"
                for time_type, duration in process_info['processing_time'].items():
                    response += f"• {time_type.title()}: {duration}\n"
            else:
                response += f"\n\nProcessing Time: {process_info['processing_time']}"

        # Add where to apply if available
        if 'where_to_apply' in process_info:
            response += f"\n\nWhere to Apply: {process_info['where_to_apply']}"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideDocumentsList(Action):
    def name(self) -> Text:
        return "action_provide_documents_list"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like the required documents?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have document requirements for {cert_type}.")
            return []

        # Handle different document structures
        docs = []
        if 'documents_needed' in cert_info:
            if isinstance(cert_info['documents_needed'], list):
                docs = cert_info['documents_needed']
            elif isinstance(cert_info['documents_needed'], dict):
                for category, items in cert_info['documents_needed'].items():
                    if isinstance(items, list):
                        docs.extend(items)
                    else:
                        docs.append(items)
        elif 'required_docs' in cert_info:  # Alternative field name
            docs = cert_info['required_docs']

        if not docs:
            dispatcher.utter_message(text=f"Sorry, document requirements not available for {cert_type}.")
            return []

        response = f"Documents Required for {cert_info.get('name', cert_type.title())}:\n\n"
        response += "\n".join([f"• {doc}" for doc in docs])
        dispatcher.utter_message(text=response)
        return []


class ActionProvideCostInfo(Action):
    def name(self) -> Text:
        return "action_provide_cost_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like fee information?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have fee details for {cert_type}.")
            return []

        # Handle different fee structures
        fees = {}
        if 'cost' in cert_info:
            fees = cert_info['cost']
        elif 'fee_structure' in cert_info:
            fees = cert_info['fee_structure']
        elif 'fees' in cert_info:
            fees = cert_info['fees']

        # Special handling for passport tatkal fees
        if cert_type.lower() in ['passport', 'passports'] and 'tatkal_passport_procedure' in cert_info:
            tatkal_fees = cert_info['tatkal_passport_procedure'].get('processing_fee')
            if tatkal_fees:
                fees['tatkal'] = tatkal_fees

        if not fees:
            dispatcher.utter_message(text=f"Fee information not available for {cert_type}.")
            return []

        response = f"Fees for {cert_info.get('name', cert_type.title())}:\n\n"

        if isinstance(fees, dict):
            for fee_type, amount in fees.items():
                if isinstance(amount, dict):  # Nested fee structure
                    response += f"{fee_type.replace('_', ' ').title()}:\n\n"
                    for sub_type, sub_amount in amount.items():
                        response += f"• {sub_type.replace('_', ' ').title()}: {sub_amount}\n"
                else:
                    response += f"• {fee_type.replace('_', ' ').title()}: {amount}\n"
        else:
            response += f"• Standard Fee: {fees}"

        dispatcher.utter_message(text=response)
        return []


# Additional specialized actions for passport and driving license
class ActionProvidePassportTatkalInfo(Action):
    def name(self) -> Text:
        return "action_provide_passport_tatkal_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cert_info = CERT_DATA.get('passport') or CERT_DATA.get('passports')
        if not cert_info or 'tatkal_passport_procedure' not in cert_info:
            dispatcher.utter_message(text="Sorry, I don't have Tatkal passport information available.")
            return []

        tatkal = cert_info['tatkal_passport_procedure']
        response = (
                f"**Tatkal Passport Procedure:**\n\n"
                f"**Eligibility:** {tatkal.get('eligibility', 'N/A')}\n\n"
                f"**Additional Documents Needed:**\n" +
                "\n".join([f"• {doc}" for doc in tatkal.get('additional_documents_needed', [])]) + "\n\n"
                                                                                                   f"**Processing Fee:** {tatkal.get('processing_fee', 'N/A')}\n"
                                                                                                   f"**Processing Time:** {tatkal.get('processing_time', 'N/A')}"
        )
        dispatcher.utter_message(text=response)
        return []


class ActionProvideLicenseTypes(Action):
    def name(self) -> Text:
        return "action_provide_license_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_info = CERT_DATA.get('driving license') or CERT_DATA.get('driving_license')
        if not cert_info or 'types_of_license' not in cert_info:
            dispatcher.utter_message(text="Sorry, I don't have driving license type information available.")
            return []

        response = "Types of Driving Licenses:\n\n"
        for l_type, l_desc in cert_info['types_of_license'].items():
            response += f"• {l_type.replace('_', ' ').title()}: {l_desc}\n"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideDuplicateInfo(Action):
    def name(self) -> Text:
        return "action_provide_duplicate_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate do you need duplicate information?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))

        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have duplicate certificate details for {cert_type}.")
            return []

        # Handle different structures
        dup_info = None
        if 'duplicate_certificate' in cert_info:
            dup_info = cert_info['duplicate_certificate']
        elif 'lost_or_damaged_passport' in cert_info:  # For passport
            dup_info = cert_info['lost_or_damaged_passport']

        if not dup_info:
            dispatcher.utter_message(text=f"Duplicate process not available for {cert_type}.")
            return []

        response = f"Process for Duplicate {cert_info.get('name', cert_type.title())}:\n\n"

        if 'how_to_get' in dup_info:  # Birth certificate structure
            response += "\n".join([f"• {step}" for step in dup_info['how_to_get']])
        elif 'how_to_replace' in dup_info:  # Passport structure
            response += "\n".join([f"• {step}" for step in dup_info['how_to_replace']])

        if 'processing_time' in dup_info:
            response += f"\n\nProcessing Time: {dup_info['processing_time']}"
        if 'cost' in dup_info:
            response += f"\nCost: ₹{dup_info['cost']}"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideIssuingAuthority(Action):
    def name(self) -> Text:
        return "action_provide_issuing_authority"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="Please specify which certificate's issuing authority you need.")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))

        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have issuing authority information for {cert_type}.")
            return []

        # Handle different field names for issuing authority
        issuing_auth = cert_info.get('issuing_authority') or cert_info.get('issued_by') or cert_info.get(
            'issuing_office')

        if not issuing_auth:
            dispatcher.utter_message(text=f"Issuing authority information not available for {cert_type}.")
            return []

        response = (
            f"**Issuing Authority for {cert_info.get('name', cert_type.title())}:**\n\n"
            f"{issuing_auth}"
        )
        dispatcher.utter_message(text=response)
        return []


class ActionCheckEligibility(Action):
    def name(self) -> Text:
        return "action_check_eligibility"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like to check eligibility?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info or 'eligibility' not in cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have eligibility criteria for {cert_type}.")
            return []

        eligibility = cert_info['eligibility']
        response = f"Eligibility for {cert_info.get('name', cert_type.title())}:**\n\n"

        # Special handling for driving license
        if cert_type.lower() in ['driving license', 'driving_license']:
            response += "Learner's License:\n"
            if 'age_requirement' in eligibility.get('learner_license', {}):
                for vehicle, requirement in eligibility['learner_license']['age_requirement'].items():
                    response += f"• {vehicle.replace('_', ' ').title()}: {requirement}\n"
            if 'other_requirements' in eligibility.get('learner_license', {}):
                response += f"\nOther Requirements:\n• {eligibility['learner_license']['other_requirements']}"

            response += "\n\nPermanent License:\n"
            if 'requirements' in eligibility.get('permanent_license', {}):
                response += f"• {eligibility['permanent_license']['requirements']}"
        else:
            # Standard handling for other certificates
            if isinstance(eligibility, dict):
                for key, value in eligibility.items():
                    if isinstance(value, dict):
                        response += f"**{key.replace('_', ' ').title()}:**\n"
                        for sub_key, sub_value in value.items():
                            response += f"• {sub_key.replace('_', ' ').title()}: {sub_value}\n"
                    else:
                        response += f"• {key.replace('_', ' ').title()}: {value}\n"
            else:
                response += str(eligibility)

        dispatcher.utter_message(text=response)
        return []


class ActionProvidePassportTypes(Action):
    def name(self) -> Text:
        return "action_provide_passport_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_info = CERT_DATA.get('passport') or CERT_DATA.get('passports')
        if not cert_info or 'types_of_passport' not in cert_info:
            dispatcher.utter_message(text="Sorry, I don't have passport type information available.")
            return []

        response = "Types of Passports:\n\n"
        for p_type, p_desc in cert_info['types_of_passport'].items():
            response += f"• {p_type.replace('_', ' ').title()}: {p_desc}\n"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideOnlineApplicationInfo(Action):
    def name(self) -> Text:
        return "action_provide_online_application_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like online application information?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))

        # Check different possible locations for online info
        online_portal = None
        if 'online_portal' in cert_info:
            online_portal = cert_info['online_portal']
        elif 'application_process' in cert_info and 'where_to_apply' in cert_info['application_process']:
            if 'http' in cert_info['application_process']['where_to_apply']:
                online_portal = cert_info['application_process']['where_to_apply']
        elif 'online_services' in cert_info and 'apply_online' in cert_info['online_services']:
            online_portal = cert_info['online_services']['apply_online']

        if not online_portal:
            dispatcher.utter_message(text=f"Sorry, online application is not available for {cert_type}.")
            return []

        response = (
            f"You can apply for {cert_info.get('name', cert_type)} online at:\n"
            f"{online_portal}\n\n"
            "**Steps:**\n"
            "1. Visit the portal\n"
            "2. Create an account\n"
            "3. Fill the application form\n"
            "4. Upload required documents\n"
            "5. Pay the fees\n"
            "6. Track your application"
        )

        dispatcher.utter_message(text=response)
        return []



class ActionProvideProcessingTime(Action):
    def name(self) -> Text:
        return "action_provide_processing_time"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like processing time information?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have processing time details for {cert_type}.")
            return []

        response = f"Processing Time for {cert_info.get('name', cert_type.title())}:\n\n"

        # Handle different JSON structures for processing time
        processing_info = None

        # Case 1: Direct processing_time field
        if 'processing_time' in cert_info:
            processing_info = cert_info['processing_time']

        # Case 2: Nested in application_process
        elif 'application_process' in cert_info and isinstance(cert_info['application_process'],
                                                               dict) and 'processing_time' in cert_info[
            'application_process']:
            processing_info = cert_info['application_process']['processing_time']

        # Case 3: Special cases (like passport tatkal)
        elif cert_type.lower() in ['passport', 'passports'] and 'tatkal_passport_procedure' in cert_info:
            processing_info = {
                'normal': cert_info.get('processing_time', 'Not specified'),
                'tatkal': cert_info['tatkal_passport_procedure'].get('processing_time', '1-3 days')
            }

        if not processing_info:
            dispatcher.utter_message(text=f"Processing time information not available for {cert_type}.")
            return []

        # Format the response based on data type
        if isinstance(processing_info, dict):
            for time_type, duration in processing_info.items():
                response += f"• {time_type.replace('_', ' ').title()}: {duration}\n"
        elif isinstance(processing_info, list):
            response += "\n".join([f"• {item}" for item in processing_info])
        else:
            response += f"• Standard Processing: {processing_info}"

        # Add additional time-related information if available
        if 'duplicate_card' in cert_info and 'processing_time' in cert_info['duplicate_card']:
            response += f"\n• Duplicate Processing: {cert_info['duplicate_card']['processing_time']}"

        if 'correction_or_update' in cert_info and 'processing_time' in cert_info['correction_or_update']:
            response += f"\n• Correction Processing: {cert_info['correction_or_update']['processing_time']}"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideRationCardTypes(Action):
    def name(self) -> Text:
        return "action_provide_ration_card_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_info = CERT_DATA.get('ration card') or CERT_DATA.get('ration_card')
        if not cert_info or 'types_of_ration_cards' not in cert_info:
            dispatcher.utter_message(text="Sorry, ration card type information isn't available.")
            return []

        response = (
            "**Types of Ration Cards:**\n\n"
            "The Public Distribution System issues these card types:\n"
        )

        for card_type, description in cert_info['types_of_ration_cards'].items():
            response += f"\n• **{card_type.upper()}**: {description}"

        dispatcher.utter_message(text=response)
        return []


class ActionProvideValidityInfo(Action):
    def name(self) -> Text:
        return "action_provide_validity_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="For which certificate would you like validity information?")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have validity information for {cert_type}.")
            return []

        # Handle different validity structures
        if 'validity' in cert_info:
            validity = cert_info['validity']
        elif 'expiry' in cert_info:
            validity = cert_info['expiry']
        else:
            validity = "Typically valid until cancelled or updated"

        response = (
            f"**Validity Information for {cert_info.get('name', cert_type.title())}:**\n\n"
            f"{validity}"
        )
        dispatcher.utter_message(text=response)
        return []


class ActionProvideElectricityBillInfo(Action):
    def name(self) -> Text:
        return "action_provide_electricity_bill_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = (
            "**Electricity Bill Information:**\n\n"
            "An official document showing electricity consumption and payment details. "
            "Issued by your State Electricity Board.\n\n"
            "You can ask about:\n"
            "• New connections\n• Bill payment\n• Name changes\n"
            "• Duplicate bills\n• Meter issues\n• Online services"
        )
        dispatcher.utter_message(text=response)
        return [SlotSet("certificate_type", "electricity_bill")]


class ActionProvideNewElectricityConnection(Action):
    def name(self) -> Text:
        return "action_provide_new_electricity_connection"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cert_info = CERT_DATA.get('electricity_bill')
        if not cert_info or 'new_connection' not in cert_info:
            dispatcher.utter_message(text="New connection information isn't available.")
            return []

        nc_info = cert_info['new_connection']
        response = (
                "**New Electricity Connection Process:**\n\n"
                "**Eligibility:**\n• " + nc_info['eligibility'] + "\n\n"
                                                                  "**Required Documents:**\n" +
                "\n".join([f"• {doc}" for doc in nc_info['documents_needed']]) + "\n\n"
                                                                                 "**Steps:**\n" +
                "\n".join([f"{i + 1}. {step}" for i, step in enumerate(nc_info['steps'])]) + "\n\n"
                                                                                             "**Cost:**\n" +
                f"• Domestic: {nc_info['cost']['domestic']}\n" +
                f"• Commercial: {nc_info['cost']['commercial']}\n\n"
                f"**Processing Time:** {nc_info['processing_time']}\n"
                f"**Apply at:** {nc_info['where_to_apply']}"
        )
        dispatcher.utter_message(text=response)
        return []


class ActionProvideRenewalInfo(Action):
    """Handles renewal queries for all certificates with smart fallbacks"""

    def name(self) -> Text:
        return "action_provide_renewal_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="Please specify which certificate you want to renew.")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have information about {cert_type} certificates.")
            return []

        # Default template that works for all certificates
        response = f"Renewal Information for {cert_info.get('name', cert_type.title())}:\n\n"

        # 1. Check for explicit renewal info first
        renewal_info = (cert_info.get('renewal_process') or
                        cert_info.get('renewal') or
                        cert_info.get('license_renewal') or
                        cert_info.get('passport_renewal') or
                        {})

        # 2. Build response sections with smart fallbacks
        if isinstance(renewal_info, dict):
            # Steps section
            if 'steps' in renewal_info:
                response += "Steps:\n" + "\n".join([f"• {step}" for step in renewal_info['steps']]) + "\n\n"
            else:
                response += "Standard Renewal Process:\n\n• Visit issuing authority's portal\n• Submit renewal application\n• Pay applicable fees\n• Receive renewed document\n\n"

            # Documents section
            if 'documents_needed' in renewal_info:
                response += "Documents Required:\n" + "\n".join(
                    [f"• {doc}" for doc in renewal_info['documents_needed']]) + "\n\n"
            elif 'documents_needed' in cert_info:  # Fallback to general documents
                response += "Typically Required Documents:\n" + "\n".join(
                    [f"• {doc}" for doc in cert_info['documents_needed']]) + "\n\n"

            # Fees section
            if 'fees' in renewal_info:
                response += self._format_fees(renewal_info['fees'])
            elif 'cost' in cert_info:  # Fallback to general fees
                response += "Typical Fees:\n" + self._format_fees(cert_info['cost'])

            # Processing time
            processing_time = renewal_info.get('processing_time',
                                               cert_info.get('processing_time',
                                                             "Usually 15-30 working days"))
            response += f"\nProcessing Time: {processing_time}"

        elif isinstance(renewal_info, list):
            response += "Renewal Steps:\n" + "\n".join([f"• {step}" for step in renewal_info])
        else:
            response += renewal_info if renewal_info else "Standard renewal process applies. Please contact the issuing authority for specific procedures."

        # Special cases
        if cert_type.lower() in ['passport', 'passports']:
            response += "\n\nℹ️ Passport renewal requires submission of your old passport."
        elif cert_type.lower() in ['driving license', 'driving_license']:
            response += "\n\nℹ️ License renewal may require a medical certificate for applicants over 40."

        dispatcher.utter_message(text=response)
        return []

    def _format_fees(self, fees: Any) -> Text:
        """Helper method to format fee structures consistently"""
        fee_text = "**Fees:**\n"
        if isinstance(fees, dict):
            for fee_type, amount in fees.items():
                if isinstance(amount, dict):  # Nested fee structure
                    fee_text += f"  {fee_type.replace('_', ' ').title()}:\n"
                    for sub_type, sub_amount in amount.items():
                        fee_text += f"    • {sub_type.replace('_', ' ').title()}: ₹{sub_amount}\n"
                else:
                    fee_text += f"• {fee_type.replace('_', ' ').title()}: ₹{amount}\n"
        else:
            fee_text += f"• Standard Fee: ₹{fees}\n"
        return fee_text + "\n"


class ActionProvideCorrectionInfo(Action):
    """Handles correction/update procedures for all certificate types with smart defaults"""

    def name(self) -> Text:
        return "action_provide_correction_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type:
            dispatcher.utter_message(text="Please specify which certificate needs corrections.")
            return []

        cert_info = CERT_DATA.get(cert_type.lower()) or CERT_DATA.get(cert_type.lower().replace(' ', '_'))
        if not cert_info:
            dispatcher.utter_message(text=f"Sorry, I don't have information about {cert_type} certificates.")
            return []

        # Try multiple field names for correction info
        correction_info = self._get_correction_info(cert_info, cert_type)

        response = f"**Correction/Update Process for {cert_info.get('name', cert_type.title())}:**\n\n"
        response += self._build_correction_response(cert_info, correction_info, cert_type)

        dispatcher.utter_message(text=response)
        return []

    def _get_correction_info(self, cert_info: Dict, cert_type: Text) -> Dict:
        """Extracts correction info from certificate data with priority order"""
        correction_fields = [
            'correction_process',
            'correction_procedure',
            'update_process',
            'modification',
            'changes'
        ]

        for field in correction_fields:
            if field in cert_info:
                return cert_info[field]

        # Special cases for specific certificates
        if cert_type.lower() in ['passport', 'passports']:
            return {
                'steps': [
                    "Submit application through Passport Seva Portal",
                    "Visit PSK with original documents",
                    "Pay applicable fees"
                ],
                'documents_needed': [
                    "Original passport",
                    "Proof of correct information"
                ],
                'fees': {
                    'minor_changes': 500,
                    'major_changes': "May require re-application"
                }
            }
        elif cert_type.lower() in ['driving license', 'driving_license']:
            return {
                'steps': [
                    "Submit Form 1 at RTO",
                    "Provide supporting documents",
                    "Pay correction fees"
                ],
                'fees': 200
            }

        return {}

    def _build_correction_response(self, cert_info: Dict, correction_info: Dict, cert_type: Text) -> Text:
        """Constructs the response message with smart fallbacks"""
        response = ""

        # 1. Steps/Process
        if isinstance(correction_info, dict) and 'steps' in correction_info:
            response += "**Procedure:**\n" + "\n".join([f"• {step}" for step in correction_info['steps']]) + "\n\n"
        elif isinstance(correction_info, list):
            response += "**Steps:**\n" + "\n".join([f"• {step}" for step in correction_info]) + "\n\n"
        else:
            response += "**Standard Process:**\n• Visit issuing authority\n• Submit correction form\n• Provide supporting documents\n• Pay applicable fees\n\n"

        # 2. Documents
        docs = self._get_document_list(correction_info, cert_info)
        response += f"**Required Documents:**\n{docs}\n\n" if docs else ""

        # 3. Fees
        fees = self._get_fee_info(correction_info, cert_info)
        response += fees if fees else ""

        # 4. Processing Time
        processing_time = self._get_processing_time(correction_info, cert_info)
        response += f"**Processing Time:** {processing_time}\n\n"

        # 5. Special Notes
        special_notes = self._get_special_notes(cert_type)
        response += special_notes if special_notes else ""

        return response

    def _get_document_list(self, correction_info: Dict, cert_info: Dict) -> Text:
        """Extracts document requirements with fallbacks"""
        if isinstance(correction_info, dict) and 'documents_needed' in correction_info:
            return "\n".join([f"• {doc}" for doc in correction_info['documents_needed']])
        elif 'documents_needed' in cert_info:
            return "\n".join([f"• {doc}" for doc in cert_info['documents_needed']])
        elif 'required_docs' in cert_info:
            return "\n".join([f"• {doc}" for doc in cert_info['required_docs']])
        return ""

    def _get_fee_info(self, correction_info: Dict, cert_info: Dict) -> Text:
        """Formats fee information consistently"""
        fees = None
        if isinstance(correction_info, dict) and 'fees' in correction_info:
            fees = correction_info['fees']
        elif 'cost' in cert_info:
            fees = cert_info['cost']
        elif 'fee_structure' in cert_info:
            fees = cert_info['fee_structure']

        if not fees:
            return ""

        fee_text = "**Fees:**\n"
        if isinstance(fees, dict):
            for fee_type, amount in fees.items():
                fee_text += f"• {fee_type.replace('_', ' ').title()}: ₹{amount}\n" if isinstance(amount, (
                int, float)) else f"• {fee_type.replace('_', ' ').title()}: {amount}\n"
        else:
            fee_text += f"• Standard Fee: ₹{fees}\n"
        return fee_text + "\n"

    def _get_processing_time(self, correction_info: Dict, cert_info: Dict) -> Text:
        """Gets processing time with fallbacks"""
        if isinstance(correction_info, dict) and 'processing_time' in correction_info:
            return correction_info['processing_time']
        elif 'processing_time' in cert_info:
            return cert_info['processing_time']
        elif 'application_process' in cert_info and isinstance(cert_info['application_process'],
                                                               dict) and 'processing_time' in cert_info[
            'application_process']:
            return cert_info['application_process']['processing_time']
        return "Typically 7-15 working days"

    def _get_special_notes(self, cert_type: Text) -> Text:
        """Adds certificate-specific notes"""
        notes = {
            'passport': "ℹ️ Major changes like name corrections may require fresh application with supporting documents.",
            'passports': "ℹ️ Major changes like name corrections may require fresh application with supporting documents.",
            'driving_license': "ℹ️ For address changes, bring two proofs of new address. Photo changes require fresh photographs.",
            'driving license': "ℹ️ For address changes, bring two proofs of new address. Photo changes require fresh photographs.",
            'pan_card': "ℹ️ PAN card corrections are free for errors made by department. Other changes may incur fees.",
            'pan card': "ℹ️ PAN card corrections are free for errors made by department. Other changes may incur fees.",
            'aadhaar': "ℹ️ Aadhaar details can be updated online for free (limited changes) or at enrollment centers.",
            'voter_id': "ℹ️ Voter ID corrections require submission of Form 8 along with supporting documents."
        }
        return notes.get(cert_type.lower(), "")


class ActionProvideLandRegistrationTypes(Action):
    def name(self) -> Text:
        return "action_provide_land_registration_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_info = CERT_DATA.get('land_registration', {})
        types_info = cert_info.get('types_of_land_registration', {})

        if not types_info:
            dispatcher.utter_message(text="Land registration types information isn't available.")
            return []

        response = "**Types of Land Registration:**\n\n"
        for deed_type, details in types_info.items():
            response += (
                f"• **{deed_type.replace('_', ' ').title()}**\n"
                f"  - Purpose: {details.get('definition', 'N/A')}\n"
                f"  - Used For: {details.get('applicable_for', 'N/A')}\n"
                f"  - Processing Time: {details.get('processing_time', 'N/A')}\n\n"
            )

        response += "You can ask about specific deed types like 'Tell me about sale deed requirements'"
        dispatcher.utter_message(text=response)
        return [SlotSet("certificate_type", "land_registration")]


class ActionProvideLandRegistrationTypes(Action):
    def name(self) -> Text:
        return "action_provide_land_registration_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cert_info = CERT_DATA.get('land_registration', {})
        types_info = cert_info.get('types_of_land_registration', {})

        response = "**Types of Land Registration:**\n\n"

        for deed_type, details in types_info.items():
            response += (
                f"• **{deed_type.replace('_', ' ').title()}**:\n"
                f"  - {details.get('definition', '')}\n"
                f"  - Applicable for: {details.get('applicable_for', '')}\n"
                f"  - Processing Time: {details.get('processing_time', '')}\n\n"
            )

        dispatcher.utter_message(text=response)
        return [SlotSet("certificate_type", "land_registration")]


class ActionProvideLandRegistrationStampDuty(Action):
    def name(self) -> Text:
        return "action_provide_land_registration_stamp_duty"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_info = CERT_DATA.get('land_registration', {})
        duty_info = cert_info.get('stamp_duty_and_fees', {})

        if not duty_info:
            dispatcher.utter_message(text="Stamp duty information isn't available.")
            return []

        response = (
            "**Stamp Duty for Land Registration:**\n\n"
            f"{duty_info.get('definition', 'Government tax on property registration')}\n\n"
            "**Applicable Rates:**\n"
        )

        for deed_type, rate in duty_info.get('stamp_duty_rates', {}).items():
            response += f"• {deed_type.replace('_', ' ').title()}: {rate}\n"

        response += (
            f"\n**Registration Fees:** {duty_info.get('registration_fees', 'N/A')}\n"
            f"**Other Charges:** {duty_info.get('other_charges', 'N/A')}\n\n"
            "Note: Rates vary by state. Check your local registration office for exact amounts."
        )

        dispatcher.utter_message(text=response)
        return [SlotSet("certificate_type", "land_registration")]


class ActionProvideMutationInfo(Action):
    def name(self) -> Text:
        return "action_provide_mutation_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cert_info = CERT_DATA.get('land_registration', {})
        mutation_info = cert_info.get('mutation_process', {})

        response = (
                f"**Property Mutation Process:**\n\n"
                f"{mutation_info.get('definition', 'Updating government land records')}\n\n"
                "**When Required:**\n" +
                "\n".join([f"• {item}" for item in mutation_info.get('when_required', [])]) + "\n\n"
                                                                                              "**Steps:**\n" +
                "\n".join([f"{i + 1}. {step}" for i, step in enumerate(mutation_info.get('steps', []))]) + "\n\n"
                                                                                                           f"**Processing Time:** {mutation_info.get('processing_time', '')}\n"
                                                                                                           f"**Where to Apply:** {mutation_info.get('where_to_apply', '')}"
        )

        dispatcher.utter_message(text=response)
        return [SlotSet("certificate_type", "land_registration")]


class ActionProvideEncumbranceInfo(Action):
    def name(self) -> Text:
        return "action_provide_encumbrance_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cert_info = CERT_DATA.get('land_registration', {})
        ec_info = cert_info.get('encumbrance_certificate', {})

        response = (
                f"**Encumbrance Certificate (EC):**\n\n"
                f"{ec_info.get('definition', 'Document verifying property is free from legal disputes')}\n\n"
                "**Importance:**\n" +
                "\n".join([f"• {item}" for item in ec_info.get('importance', [])]) + "\n\n"
                                                                                     "**How to Obtain:**\n" +
                "\n".join([f"{i + 1}. {step}" for i, step in enumerate(ec_info.get('how_to_obtain', []))]) + "\n\n"
                                                                                                             f"**Processing Time:** {ec_info.get('processing_time', '')}\n"
                                                                                                             f"**Apply At:** {ec_info.get('where_to_apply', '')}"
        )

        dispatcher.utter_message(text=response)
        return [SlotSet("certificate_type", "land_registration")]


class ActionProvideLandRegistrationDetails(Action):
    def name(self) -> Text:
        return "action_provide_land_registration_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cert_type = tracker.get_slot("certificate_type")
        if not cert_type or cert_type.lower() != "land_registration":
            dispatcher.utter_message(text="Please specify you're asking about land registration.")
            return []

        deed_type = next(tracker.get_latest_entity_values("deed_type"), "").lower()
        cert_info = CERT_DATA.get('land_registration', {})
        types_info = cert_info.get('types_of_land_registration', {})

        if not deed_type or deed_type not in types_info:
            dispatcher.utter_message(text="Please specify which type of land registration (sale deed, gift deed, etc.)")
            return []

        details = types_info[deed_type]

        response = (
                f"**{deed_type.replace('_', ' ').title()} Details:**\n\n"
                f"**Definition:** {details.get('definition', '')}\n\n"
                f"**Applicable For:** {details.get('applicable_for', '')}\n\n"
                "**Requirements:**\n" +
                "\n".join([f"• {req}" for req in details.get('requirements', [])]) + "\n\n"
                                                                                     f"**Processing Time:** {details.get('processing_time', '')}"
        )

        dispatcher.utter_message(text=response)
        return []