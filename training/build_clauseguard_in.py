# Build the ClauseGuard-IN dataset of Indian agreement clauses

import random
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED = 42

SLOTS = {
    "rent": ["Rs. 12,000", "Rs. 15,500", "Rs. 18,000", "Rs. 22,000", "Rs. 9,500", "Rs. 26,000"],
    "dep": ["Rs. 36,000", "Rs. 54,000", "Rs. 60,000", "Rs. 1,00,000", "Rs. 45,000", "Rs. 75,000"],
    "lock": ["6", "3", "8", "11", "5"],
    "days": ["5", "7", "10", "15"],
    "notice_long": ["2", "3", "two", "three"],
    "notice_short": ["7", "15", "3", "10"],
    "pct": ["10", "8", "12", "15", "20"],
    "small_pct": ["5", "6"],
    "esc": ["11", "6", "12"],
    "unit": ["12", "15", "14"],
    "penalty_months": ["two", "three", "2"],
    "refund_days": ["7", "15", "30"],
    "city": ["Pune", "Mumbai", "Bengaluru", "Hyderabad", "Nashik", "Nagpur", "Chennai", "Thane"],
    "farcity": ["Kolkata", "New Delhi", "Guwahati", "Lucknow", "Chandigarh", "Bhopal"],
    "owner": ["Ramesh Kulkarni", "Sunita Deshpande", "Anil Bhosale", "Kavita Iyer", "Prakash Jadhav"],
    "tenant": ["Rohan Patil", "Sneha Joshi", "Aditya Rao", "Priya Nair", "Karan Mehta"],
    "addr": ["Kothrud, Pune", "Andheri East, Mumbai", "Wakad, Pune", "Indiranagar, Bengaluru", "Baner, Pune"],
    "flat": ["B-203", "A-1104", "C-12", "D-501", "702"],
    "bldg": ["Shubham Residency", "Sai Krupa Apartments", "Green Valley", "Sunshine Heights", "Om Sai Park"],
    "area": ["Kothrud", "Hadapsar", "Wakad", "Aundh", "Kharadi", "Viman Nagar"],
    "sqft": ["550", "650", "720", "900", "480"],
    "day": ["1st", "5th", "10th", "15th", "20th"],
    "month": ["January", "March", "June", "July", "September", "November"],
    "year": ["2026", "2027"],
    "date": ["1 July 2026", "15 August 2026", "1 September 2026", "1 January 2027"],
    "date2": ["31 May 2027", "14 July 2027", "31 July 2027", "30 November 2027"],
    "nth": ["5th", "7th", "10th"],
    "n": ["3", "4", "2"],
    "n2": ["4", "5", "6"],
    "bond_years": ["two", "2", "three", "1.5"],
    "bond_months": ["18", "24", "12", "30"],
    "bond": ["Rs. 2,00,000", "Rs. 1,50,000", "Rs. 3,00,000", "Rs. 1,00,000", "Rs. 2,50,000"],
    "nc_months": ["12", "24", "18", "6"],
    "nc_years": ["two", "one", "three"],
    "notice_days": ["90", "60", "120"],
    "company_notice": ["7", "15", "30"],
    "notice_equal": ["30", "60"],
    "role": ["Associate Software Engineer", "Graduate Engineer Trainee", "Systems Engineer", "Junior Data Analyst",
             "Software Developer Trainee"],
    "company": ["Zentrix Technologies Pvt. Ltd.", "Nimbus Infosoft Pvt. Ltd.", "Vertex Digital Services LLP",
                "Orbit Softworks Pvt. Ltd.", "Kalpa Systems Pvt. Ltd."],
    "ctc": ["Rs. 4,20,000", "Rs. 3,60,000", "Rs. 6,00,000", "Rs. 5,25,000"],
    "leaves": ["18", "21", "24", "15"],
    "ins": ["Rs. 3,00,000", "Rs. 5,00,000", "Rs. 2,00,000"],
    "app": ["Chatterly", "SnapKart", "FitBuddy", "QuickLoanz", "StudyNest", "the App"],
    "small_amt": ["Rs. 1,000", "USD 50", "Rs. 500", "USD 100"],
    "foreign_state": ["Delaware", "California", "New York"],
    "foreign_country": ["Singapore", "the State of California, USA", "England and Wales"],
    "foreign_city": ["Singapore", "San Francisco", "London"],
    "arb_body": ["the Singapore International Arbitration Centre", "JAMS", "the London Court of International Arbitration"],
    "email": ["grievance@studynest.example", "support@fitbuddy.example", "privacy@chatterly.example"],
}

R, O, T = "rental", "offer_letter", "tos"

# empty label means a fair clause
TEMPLATES = [
    # rental: risky
    (R, "deposit_forfeiture|service_bond_lock_in", "If the [Licensee|Tenant] vacates the [premises|flat] before the expiry of the lock-in period of {lock} months, the entire security deposit of {dep} shall stand forfeited."),
    (R, "deposit_forfeiture", "The [Licensor|Owner] shall be entitled to deduct any amount from the security deposit as the [Licensor|Owner] deems fit, and such decision shall be final and binding on the [Licensee|Tenant]."),
    (R, "deposit_forfeiture", "The security deposit shall be refunded only after the [Licensor|Owner] finds a new [licensee|tenant] for the premises, and no interest shall be payable on it."),
    (R, "deposit_forfeiture", "In case of any delay in payment of rent beyond {days} days, the [Licensor|Owner] may forfeit the security deposit in full without further notice."),
    (R, "deposit_forfeiture", "A deduction of one month's rent shall be made from the deposit towards painting and cleaning charges [irrespective of|regardless of] the condition of the premises at the time of vacating."),
    (R, "deposit_forfeiture|one_sided_notice", "No part of the deposit shall be returned if the [Licensee|Tenant] fails to give {notice_long} months' notice before vacating, while the [Licensor|Owner] may end the licence at any time."),
    (R, "deposit_forfeiture", "If any damage is found at the time of vacating, the [Licensor|Owner] may adjust the cost of repairs from the deposit at rates fixed solely by the [Licensor|Owner]."),
    (R, "rent_escalation", "The monthly [rent|licence fee] shall be increased by {pct}% every {esc} months during the term of this agreement."),
    (R, "rent_escalation|unilateral_change", "The [Licensor|Owner] reserves the right to revise the [rent|licence fee] at any time during the licence period depending on market conditions."),
    (R, "rent_escalation", "On renewal, the rent shall be enhanced by such percentage as the [Licensor|Owner] may decide, and the [Licensee|Tenant] shall have no objection to the same."),
    (R, "rent_escalation|unilateral_change", "Maintenance charges, society charges and any increase in property tax shall be borne by the [Licensee|Tenant] in addition to the rent, as revised by the [Licensor|Owner] from time to time."),
    (R, "rent_escalation", "Electricity shall be charged at Rs. {unit} per unit as fixed by the [Licensor|Owner], and this rate may be increased by the [Licensor|Owner] without notice."),
    (R, "one_sided_notice", "The [Licensee|Tenant] shall give {notice_long} months' written notice to vacate, whereas the [Licensor|Owner] may terminate this agreement by giving {notice_short} days' notice."),
    (R, "one_sided_notice|unilateral_termination", "The [Licensor|Owner] may ask the [Licensee|Tenant] to vacate the premises at any time by giving {notice_short} days' notice, but the [Licensee|Tenant] must give not less than {notice_long} months' notice."),
    (R, "service_bond_lock_in", "There shall be a lock-in period of {lock} months during which the [Licensee|Tenant] cannot terminate this agreement; if the [Licensee|Tenant] leaves during the lock-in period, rent for the remaining lock-in period shall be payable."),
    (R, "service_bond_lock_in", "The [Licensee|Tenant] agrees that the first {lock} months of this agreement are a lock-in period and shall pay the full rent for those months even if the premises are vacated earlier."),
    (R, "service_bond_lock_in|deposit_forfeiture", "If the [Licensee|Tenant] wishes to leave within the first {lock} months, {penalty_months} months' rent shall be deducted from the security deposit as penalty."),
    (R, "unilateral_termination", "The [Licensor|Owner] may terminate this licence immediately and without assigning any reason, and the [Licensee|Tenant] shall vacate the premises within {notice_short} days."),
    (R, "unilateral_termination", "If the [Licensee|Tenant] is found to have guests staying overnight, the [Licensor|Owner] may cancel this agreement forthwith and take possession of the premises."),
    (R, "unilateral_termination", "Non-payment of rent for even one month shall entitle the [Licensor|Owner] to terminate this agreement and remove the belongings of the [Licensee|Tenant] from the premises."),
    (R, "unilateral_termination", "The [Licensor|Owner] shall have the right to lock the premises and disconnect electricity and water supply if the rent is not paid on the due date."),
    (R, "unilateral_change", "The [Licensor|Owner] may change the house rules, visiting hours and other terms of this agreement from time to time, and such changes shall be binding on the [Licensee|Tenant]."),
    (R, "unilateral_change", "The [Licensor|Owner] may modify the terms of this agreement by sending a message to the [Licensee|Tenant], and continued stay in the premises shall be treated as acceptance."),
    (R, "limitation_of_liability", "The [Licensor|Owner] shall not be responsible for any loss, theft or damage to the belongings of the [Licensee|Tenant] howsoever caused, including due to the negligence of the [Licensor|Owner]."),
    (R, "limitation_of_liability", "The [Licensor|Owner] shall not be liable for any injury or damage arising from defects in the building, electrical fittings, lift or water leakage."),
    (R, "jurisdiction", "All disputes arising out of this agreement shall be subject to the exclusive jurisdiction of the courts at {farcity} only."),
    (R, "arbitration", "Any dispute between the parties shall be referred to a sole arbitrator appointed by the [Licensor|Owner], and the award of such arbitrator shall be final and binding."),
    (R, "arbitration|jurisdiction", "Disputes shall be settled by arbitration under the Arbitration and Conciliation Act, 1996 with the seat of arbitration at {farcity}, and the courts at {farcity} alone shall have jurisdiction."),
    # rental: fair / neutral
    (R, "", "This Leave and Licence Agreement is made at {city} on this {day} day of {month} {year} between [Mr.|Shri] {owner}, residing at {addr}, hereinafter called the Licensor, and {tenant}, hereinafter called the Licensee."),
    (R, "", "The Licensor is the absolute owner of the flat bearing No. {flat}, {bldg}, {area}, {city}, admeasuring about {sqft} sq. ft. carpet area."),
    (R, "", "The licence is granted for a period of eleven months commencing from {date} and ending on {date2}."),
    (R, "", "The Licensee shall pay a monthly licence fee of {rent} on or before the {nth} day of every English calendar month."),
    (R, "", "The Licensee has paid an interest-free refundable security deposit of {dep}, which shall be returned at the time of vacating the premises after deducting any unpaid dues."),
    (R, "", "The premises shall be used only for residential purposes by the Licensee and the members of the Licensee's family."),
    (R, "", "The Licensee shall pay the electricity and water bills as per the actual consumption recorded on the [meter|sub-meter]."),
    (R, "", "The Licensee shall keep the premises clean and in good condition and shall not make any structural alterations without the prior written consent of the Licensor."),
    (R, "", "Either party may terminate this agreement by giving one month's written notice to the other party."),
    (R, "", "The Licensor shall carry out major repairs such as plumbing, roof leakage and electrical wiring at the Licensor's own cost within a reasonable time."),
    (R, "", "The Licensor or the Licensor's representative may inspect the premises at a reasonable hour after giving at least 24 hours' prior notice to the Licensee."),
    (R, "", "The monthly society maintenance charges and property tax shall be paid by the Licensor."),
    (R, "", "The Licensee shall not sub-let, assign or part with possession of the premises or any part of it."),
    (R, "", "The security deposit shall be refunded in full within {refund_days} days of the Licensee handing over vacant possession, after deducting unpaid bills, if any, with a written statement of deductions."),
    (R, "", "The Licensee shall abide by the rules and bye-laws of the {bldg} Co-operative Housing Society."),
    (R, "", "This agreement shall be registered with the Sub-Registrar, and the stamp duty and registration charges shall be shared equally by both parties."),
    (R, "", "The Licensor has provided the following fixtures in the flat: {n} fans, {n2} tube lights, a geyser and a modular kitchen."),
    (R, "", "The agreement may be renewed for a further period on mutually agreed terms with the written consent of both parties."),
    (R, "", "The Licensee shall hand over the premises in the same condition as received, subject to normal wear and tear."),
    (R, "", "Nothing in this agreement shall be construed as creating a tenancy in favour of the Licensee, and the Licensee shall have no right, title or interest in the premises."),
    (R, "", "Both parties have read and understood the terms of this agreement and have signed it in the presence of two witnesses."),
    (R, "", "If the licence is renewed, the licence fee for the next period may be increased by not more than {small_pct}% with the mutual written consent of both parties."),
    (R, "", "The Licensee shall be entitled to peaceful use and enjoyment of the premises during the licence period without interference from the Licensor."),
    (R, "", "Any notice under this agreement shall be given in writing and delivered by hand, registered post or e-mail to the addresses mentioned above."),
    (R, "", "The Licensee shall submit a copy of identity proof and the police verification form as required by the local police station."),
    (R, "", "Pets are allowed in the premises provided they do not cause nuisance to the neighbours."),
    (R, "", "Parking slot no. {n} in the stilt area is allotted for the use of the Licensee's two-wheeler."),
    # offer letter: risky
    (O, "service_bond_lock_in", "You will be required to sign a service agreement to serve the Company for a minimum period of {bond_years} years from the date of joining. If you leave before completing this period, you shall pay the Company an amount of {bond} as liquidated damages."),
    (O, "service_bond_lock_in", "In consideration of the training provided, you agree to work with the Company for at least {bond_months} months, failing which you [will|shall] reimburse the training cost of {bond}."),
    (O, "service_bond_lock_in", "Your original educational certificates will be retained by the Company until you complete the bond period of {bond_years} years."),
    (O, "service_bond_lock_in", "You shall submit post-dated cheques amounting to {bond} as security for the service bond, which the Company may present for payment if you resign during the bond period."),
    (O, "service_bond_lock_in|one_sided_notice", "If you resign within {bond_months} months of joining, you shall pay {bond} to the Company and also serve a notice period of {notice_days} days."),
    (O, "non_compete", "For a period of {nc_months} months after leaving the Company, you shall not join or work for any competitor, client or vendor of the Company in any capacity."),
    (O, "non_compete", "You shall not, during your employment and for {nc_years} years thereafter, engage in any business that competes with the business of the Company anywhere in India."),
    (O, "non_compete", "You agree not to accept employment with any client of the Company with whom you worked during the last {nc_months} months of your employment, for a period of one year after separation."),
    (O, "non_compete", "You shall not solicit or work for any customer of the Company for {nc_years} years after you leave, irrespective of the reason for separation."),
    (O, "one_sided_notice", "You are required to serve a notice period of {notice_days} days upon resignation, whereas the Company may terminate your employment by giving {company_notice} days' notice or salary in lieu thereof."),
    (O, "one_sided_notice|unilateral_termination", "During probation, the Company may terminate your services without notice, but you will be required to give {notice_days} days' notice if you wish to resign."),
    (O, "one_sided_notice", "The notice period of {notice_days} days cannot be bought out or waived, and any shortfall in the notice period will be recovered at twice your gross salary."),
    (O, "unilateral_change", "The Company reserves the right to change your designation, salary structure, work location, shift timings and other terms of employment at its sole discretion."),
    (O, "unilateral_change", "The policies of the Company may be amended from time to time without prior notice, and such amended policies shall form part of your terms of employment."),
    (O, "unilateral_change", "You may be transferred to any location, department, group company or client site in India or abroad as decided by the management, and refusal will be treated as misconduct."),
    (O, "unilateral_change", "Variable pay and bonus are payable at the sole discretion of the management and may be withdrawn at any time without assigning reasons."),
    (O, "unilateral_termination", "The Company may terminate your employment at any time without assigning any reason and without any notice or compensation."),
    (O, "unilateral_termination", "This offer may be withdrawn by the Company at any time before or after your joining if business requirements change."),
    (O, "broad_data_sharing", "You consent to the Company collecting, storing and sharing your personal information, including Aadhaar, PAN, bank details and family details, with its group companies, clients, verification agencies and other third parties for any business purpose."),
    (O, "broad_data_sharing", "The Company may monitor your personal devices, e-mail and social media accounts and share such information with third parties as it considers necessary."),
    (O, "broad_data_sharing", "Your photograph, name and work details may be used by the Company in marketing material and shared with clients and partners without further consent."),
    (O, "limitation_of_liability", "The Company shall not be liable for any loss of personal belongings, injury or damage suffered by you while travelling for work or at a client site."),
    (O, "arbitration", "Any dispute relating to your employment shall be referred to arbitration by an arbitrator appointed by the Company, whose decision shall be final."),
    (O, "jurisdiction", "All disputes arising out of this appointment shall be subject to the exclusive jurisdiction of the courts in {farcity}."),
    # offer letter: fair / neutral
    (O, "", "We are pleased to offer you the position of {role} at {company}, {city}, with effect from {date}."),
    (O, "", "Your annual cost to company (CTC) will be {ctc}, the break-up of which is given in Annexure A."),
    (O, "", "You will be on probation for a period of six months from the date of joining, after which your performance will be reviewed."),
    (O, "", "Your normal working hours will be from 9:30 a.m. to 6:30 p.m., Monday to Friday, with a one-hour lunch break."),
    (O, "", "You will be entitled to {leaves} days of paid leave in a calendar year, in addition to the public holidays declared by the Company."),
    (O, "", "Either party may terminate the employment by giving {notice_equal} days' written notice or salary in lieu of notice."),
    (O, "", "You will be covered under the Company's group medical insurance policy for {ins} for yourself, your spouse and children."),
    (O, "", "Provident Fund and gratuity will be applicable as per the provisions of the relevant statutes."),
    (O, "", "You shall maintain the confidentiality of all proprietary information of the Company during and after your employment."),
    (O, "", "Please report to the HR department at {company}, {city} on {date} at 9:30 a.m. with the documents listed in Annexure B."),
    (O, "", "Your appointment is subject to satisfactory background verification and a medical fitness certificate."),
    (O, "", "All intellectual property created by you in the course of your employment shall belong to the Company."),
    (O, "", "The Company will reimburse reasonable travel and accommodation expenses incurred for official work as per the travel policy."),
    (O, "", "Your salary will be credited to your bank account on the last working day of each month after statutory deductions such as income tax and professional tax."),
    (O, "", "Please sign and return a copy of this letter as a token of your acceptance within seven days of receiving it."),
    (O, "", "You will be eligible for an annual performance review, and any increment will be based on your performance and the Company's policy."),
    (O, "", "The Company follows a policy of equal opportunity and does not tolerate harassment of any kind at the workplace."),
    (O, "", "Your personal data will be processed only for employment-related purposes and in accordance with applicable data protection law."),
    (O, "", "You will undergo a classroom training programme for the first eight weeks, and the cost of this training will be borne entirely by the Company."),
    (O, "", "You will be entitled to maternity or paternity leave as per the Company policy and applicable law."),
    (O, "", "This letter, together with its annexures, constitutes the entire terms of your employment with the Company."),
    (O, "", "Please carry a copy of your degree certificate, mark sheets, two photographs and a cancelled cheque on the day of joining for verification."),
    # terms of service / privacy: risky
    (T, "contract_by_using", "By downloading, installing or using {app}, you agree to be bound by these Terms, whether or not you have read them."),
    (T, "contract_by_using|unilateral_change", "Your continued access to the platform constitutes acceptance of these Terms and any future updates to them."),
    (T, "unilateral_change", "We may revise these Terms at any time by posting the updated version on this page, and you are responsible for checking it regularly."),
    (T, "unilateral_change", "{app} reserves the right to modify or discontinue the service, its features or its pricing at any time without notice."),
    (T, "unilateral_termination", "We may suspend or terminate your account at any time, for any reason or no reason, without notice or liability to you."),
    (T, "content_removal", "We may remove or disable access to any content that you upload at our sole discretion, without giving any reason."),
    (T, "content_removal", "{app} may delete your posts, photos and messages if we believe they violate these Terms, and we are not obliged to keep a copy."),
    (T, "unilateral_termination|content_removal", "If your account is terminated, all your data, wallet balance and content may be permanently deleted without any refund."),
    (T, "limitation_of_liability", "To the maximum extent permitted by law, {app} shall not be liable for any indirect, incidental, special or consequential damages, loss of data or loss of profits."),
    (T, "limitation_of_liability", "In no event shall our total liability to you exceed {small_amt} or the amount you paid us in the last three months, whichever is lower."),
    (T, "limitation_of_liability", "The service is provided on an 'as is' and 'as available' basis without warranties of any kind, and you use it at your own risk."),
    (T, "choice_of_law", "These Terms shall be governed by the laws of the State of {foreign_state}, without regard to its conflict of law provisions."),
    (T, "choice_of_law|jurisdiction", "These Terms are governed by the laws of {foreign_country}, and you submit to the exclusive jurisdiction of the courts of {foreign_city}."),
    (T, "jurisdiction", "Any claim against {app} must be brought exclusively in the courts located at {farcity}, and you waive any objection to such venue."),
    (T, "arbitration", "All disputes shall be resolved through binding individual arbitration, and you waive your right to participate in a class action."),
    (T, "arbitration", "Any dispute arising out of the use of the app shall be finally settled by arbitration administered by {arb_body}, with the seat of arbitration at {foreign_city}."),
    (T, "broad_data_sharing", "We may share your personal information, including contacts, location and usage data, with our partners, advertisers and affiliates for marketing and other purposes."),
    (T, "broad_data_sharing", "By using the app you allow us to access your contacts, photos, microphone and location, and to share this data with third-party service providers."),
    (T, "broad_data_sharing", "Your data may be transferred to and stored in any country where we or our partners operate and may be retained indefinitely."),
    (T, "broad_data_sharing", "We may sell or transfer your personal data as part of a merger, acquisition or sale of assets, or to any third party we choose."),
    # terms of service / privacy: fair / neutral
    (T, "", "These Terms of Service explain the rules for using the {app} mobile application and website operated by {company}."),
    (T, "", "You must be at least 18 years old, or have the consent of a parent or guardian, to create an account."),
    (T, "", "You are responsible for keeping your password confidential and for all activity under your account."),
    (T, "", "You may delete your account at any time from the Settings page, and we will delete your personal data within 30 days, except where retention is required by law."),
    (T, "", "We will notify you by e-mail at least 30 days before any material change to these Terms takes effect, and you may close your account if you do not agree."),
    (T, "", "You retain ownership of the content you post and grant us a limited licence to display it within the service."),
    (T, "", "We collect only the information needed to provide the service, such as your name, e-mail address and phone number."),
    (T, "", "You can request a copy of your personal data or ask us to correct it by writing to our Grievance Officer at {email}."),
    (T, "", "You agree not to use the service to post unlawful, abusive or infringing content."),
    (T, "", "Payments are processed by a third-party payment gateway, and we do not store your full card details."),
    (T, "", "Refunds for cancelled subscriptions will be processed within 7 working days to the original payment method."),
    (T, "", "We use cookies to keep you signed in and to understand how the app is used, and you can manage cookie preferences in Settings."),
    (T, "", "If you have a complaint, our Grievance Officer will acknowledge it within 24 hours and resolve it within 15 days."),
    (T, "", "Premium features are available on a monthly subscription that you can cancel at any time."),
    (T, "", "We will not share your personal data with advertisers without your explicit consent."),
    (T, "", "We use industry-standard encryption to protect your data in transit and at rest."),
    (T, "", "Children under 13 are not permitted to use the service."),
]

TARGETS = {R: 110, O: 110, T: 80}


# fill in the template with random choices
def render(template: str, rng: random.Random) -> str:
    picks = {}

    def choose(m):
        key = m.group(1)
        if key not in picks:
            picks[key] = rng.choice(key.split("|"))
        return picks[key]

    text = re.sub(r"\[([^\]]+)\]", choose, template)
    slot_vals = {}
    for name in set(re.findall(r"\{(\w+)\}", text)):
        slot_vals[name] = rng.choice(SLOTS[name])
    return text.format(**slot_vals)


def build() -> pd.DataFrame:
    rng = random.Random(SEED)
    rows = []
    for dt, target in TARGETS.items():
        temps = [(i, t) for i, t in enumerate(TEMPLATES) if t[0] == dt]
        seen = set()
        k = 0
        while len([r for r in rows if r["doc_type"] == dt]) < target and k < target * 20:
            gid, (_, labels, tpl) = temps[k % len(temps)]
            k += 1
            text = render(tpl, rng)
            if text in seen:
                continue
            seen.add(text)
            rows.append({"text": text, "labels": labels, "doc_type": dt, "source": "team-authored", "group": gid})
    return pd.DataFrame(rows)


# 80/20 split, keeping copies of a template together
def split(df: pd.DataFrame, test_frac: float = 0.2):
    rng = random.Random(SEED)
    groups = df.groupby("group").agg(labels=("labels", "first"), doc_type=("doc_type", "first")).reset_index()
    groups["strat"] = groups["doc_type"] + ":" + groups["labels"].str.split("|").str[0].replace("", "none")
    test_groups = set()
    for _, g in groups.groupby("strat"):
        ids = list(g["group"])
        rng.shuffle(ids)
        n = round(len(ids) * test_frac)
        if n == 0 and len(ids) >= 3:
            n = 1
        test_groups.update(ids[:n])
    is_test = df["group"].isin(test_groups)
    return df[~is_test].reset_index(drop=True), df[is_test].reset_index(drop=True)


def main() -> None:
    DATA.mkdir(exist_ok=True)
    df = build()
    train, test = split(df)
    df.to_csv(DATA / "clauseguard_in.csv", index=False)
    train.to_csv(DATA / "clauseguard_in_train.csv", index=False)
    test.to_csv(DATA / "clauseguard_in_test.csv", index=False)
    safe = (df["labels"] == "").mean()
    print(f"ClauseGuard-IN: {len(df)} clauses ({safe:.0%} fair/neutral)")
    print(df["doc_type"].value_counts().to_string())
    print(f"train={len(train)}  test={len(test)}")


if __name__ == "__main__":
    main()
