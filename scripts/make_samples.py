"""Create the three demo documents in data/samples/ as .txt and .pdf (all names are fictional)."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).resolve().parent.parent / "data" / "samples"

RENTAL = """LEAVE AND LICENCE AGREEMENT

This Leave and Licence Agreement is made and executed at Pune on this 1st day of July 2026 between Mr. Vasant Gokhale, aged 58 years, residing at 14, Shantiniketan Society, Karve Road, Kothrud, Pune 411038, hereinafter called the Licensor, and Mr. Aarav Kulkarni, aged 22 years, a student residing at present at Nashik, hereinafter called the Licensee.

1. PREMISES
The Licensor is the absolute owner of Flat No. B-304, Third Floor, Shubham Residency, Paud Road, Kothrud, Pune 411038, admeasuring about 610 sq. ft. carpet area, together with the fixtures listed in Annexure I (hereinafter called the said premises).

2. PERIOD
The licence is granted for a period of 11 (eleven) months commencing from 1 July 2026 and ending on 31 May 2027, unless terminated earlier as provided in this agreement.

3. LICENCE FEE
3.1 The Licensee shall pay a monthly licence fee of Rs. 18,000 (Rupees Eighteen Thousand only) per month on or before the 5th day of every English calendar month.
3.2 The monthly licence fee shall be increased by 10% after every 6 months during the term of this agreement, and the Licensor may further revise the licence fee at any time depending on market conditions.

4. SECURITY DEPOSIT
4.1 The Licensee has paid an interest-free refundable security deposit of Rs. 54,000 (Rupees Fifty Four Thousand only) to the Licensor by bank transfer.
4.2 If the Licensee vacates the premises before the expiry of the lock-in period of 6 months, the entire security deposit of Rs. 54,000 shall stand forfeited.
4.3 The Licensor shall be entitled to deduct any amount from the security deposit as the Licensor deems fit, and such decision shall be final and binding on the Licensee.
4.4 The security deposit shall be refunded only after the Licensor finds a new licensee for the premises, and no interest shall be payable on it.

5. LOCK-IN PERIOD
There shall be a lock-in period of 6 months during which the Licensee cannot terminate this agreement; if the Licensee leaves during the lock-in period, rent for the remaining lock-in period shall also be payable.

6. NOTICE AND TERMINATION
6.1 The Licensee shall give three months' written notice to vacate the premises, whereas the Licensor may terminate this agreement by giving 15 days' notice.
6.2 The Licensor may terminate this licence immediately and without assigning any reason if the Licensee has guests staying overnight.

7. USE OF PREMISES
The premises shall be used only for residential purposes by the Licensee. The Licensee shall not sub-let, assign or part with possession of the premises or any part of it.

8. CHARGES
8.1 The Licensee shall pay the electricity and water bills as per the actual consumption recorded on the meter.
8.2 The monthly society maintenance charges and property tax shall be paid by the Licensor.

9. REPAIRS AND MAINTENANCE
9.1 The Licensee shall keep the premises clean and in good condition and shall not make any structural alterations without the prior written consent of the Licensor.
9.2 The Licensor shall carry out major repairs such as plumbing, roof leakage and electrical wiring at the Licensor's own cost within a reasonable time.

10. INSPECTION
The Licensor or the Licensor's representative may inspect the premises at a reasonable hour after giving at least 24 hours' prior notice to the Licensee.

11. LIABILITY
The Licensor shall not be responsible for any loss, theft or damage to the belongings of the Licensee howsoever caused, including due to the negligence of the Licensor.

12. HANDOVER
The Licensee shall hand over the premises in the same condition as received, subject to normal wear and tear.

13. NO TENANCY
Nothing in this agreement shall be construed as creating a tenancy in favour of the Licensee, and the Licensee shall have no right, title or interest in the premises.

14. REGISTRATION
This agreement shall be registered with the Sub-Registrar, Haveli, Pune, and the stamp duty and registration charges shall be shared equally by both parties.

15. DISPUTES
All disputes arising out of this agreement shall be subject to the exclusive jurisdiction of the courts at Kolkata only.

16. POLICE VERIFICATION
The Licensee shall submit a copy of identity proof and the police verification form as required by the Kothrud Police Station.

IN WITNESS WHEREOF the parties have signed this agreement on the day and year first written above in the presence of two witnesses.

Licensor: Vasant Gokhale          Licensee: Aarav Kulkarni
Witness 1: Meera Sathe            Witness 2: Omkar Pawar
"""

OFFER = """ZENTRIX TECHNOLOGIES PVT. LTD.
Plot 21, Rajiv Gandhi Infotech Park, Hinjewadi Phase 2, Pune 411057

Date: 10 June 2026
Ref: ZT/HR/OL/2026/0412

To,
Ms. Ishita Deshmukh
Flat 7, Gulmohar Apartments, Aundh, Pune 411007

Subject: Offer of Employment - Associate Software Engineer

Dear Ishita,

1. APPOINTMENT
We are pleased to offer you the position of Associate Software Engineer at Zentrix Technologies Pvt. Ltd., Pune, with effect from 1 August 2026, on the terms and conditions given below.

2. COMPENSATION
2.1 Your annual cost to company (CTC) will be Rs. 4,80,000 (Rupees Four Lakh Eighty Thousand only), the break-up of which is given in Annexure A.
2.2 Your salary will be credited to your bank account on the last working day of each month after statutory deductions such as income tax and professional tax.
2.3 Variable pay and bonus are payable at the sole discretion of the management and may be withdrawn at any time without assigning reasons.

3. PROBATION
You will be on probation for a period of six months from the date of joining, after which your performance will be reviewed. During probation, the Company may terminate your services without notice, but you will be required to give 90 days' notice if you wish to resign.

4. TRAINING AND SERVICE BOND
4.1 You will undergo a classroom training programme for the first eight weeks at our Pune campus.
4.2 You will be required to sign a service agreement to serve the Company for a minimum period of 2 (two) years from the date of joining. If you leave before completing this period, you shall pay the Company an amount of Rs. 2,00,000 (Rupees Two Lakh only) as liquidated damages.
4.3 Your original educational certificates will be retained by the Company until you complete the bond period of two years.

5. NOTICE PERIOD
You are required to serve a notice period of 90 days upon resignation, whereas the Company may terminate your employment by giving 15 days' notice or salary in lieu thereof. The notice period cannot be bought out or waived.

6. WORKING HOURS AND LEAVE
6.1 Your normal working hours will be from 9:30 a.m. to 6:30 p.m., Monday to Friday, with a one-hour lunch break.
6.2 You will be entitled to 18 days of paid leave in a calendar year, in addition to the public holidays declared by the Company.

7. CHANGES TO TERMS
The Company reserves the right to change your designation, salary structure, work location, shift timings and other terms of employment at its sole discretion. You may be transferred to any location, group company or client site in India or abroad as decided by the management.

8. NON-COMPETE AND NON-SOLICITATION
For a period of 12 months after leaving the Company, you shall not join or work for any competitor, client or vendor of the Company in any capacity.

9. CONFIDENTIALITY
You shall maintain the confidentiality of all proprietary information of the Company during and after your employment. All intellectual property created by you in the course of your employment shall belong to the Company.

10. PERSONAL DATA
You consent to the Company collecting, storing and sharing your personal information, including Aadhaar, PAN, bank details and family details, with its group companies, clients, verification agencies and other third parties for any business purpose.

11. BENEFITS
11.1 You will be covered under the Company's group medical insurance policy for Rs. 3,00,000 for yourself, your spouse and children.
11.2 Provident Fund and gratuity will be applicable as per the provisions of the relevant statutes.

12. VERIFICATION
Your appointment is subject to satisfactory background verification and a medical fitness certificate.

13. DISPUTES
Any dispute relating to your employment shall be referred to arbitration by an arbitrator appointed by the Company, whose decision shall be final, and the courts in New Delhi shall have exclusive jurisdiction.

14. ACCEPTANCE
Please sign and return a copy of this letter as a token of your acceptance within seven days of receiving it, and report to the HR department at Hinjewadi on 1 August 2026 at 9:30 a.m.

We look forward to welcoming you to Zentrix.

For Zentrix Technologies Pvt. Ltd.
Neha Chitale, Head - Talent Acquisition
"""

TERMS = """CHATTERLY - TERMS OF SERVICE AND PRIVACY POLICY
Last updated: 1 September 2026

These Terms of Service explain the rules for using the Chatterly mobile application and website operated by Chatterly Social Pvt. Ltd. ("Chatterly", "we", "us").

1. ACCEPTANCE OF TERMS
By downloading, installing or using Chatterly, you agree to be bound by these Terms, whether or not you have read them. Your continued access to the platform constitutes acceptance of these Terms and any future updates to them.

2. ELIGIBILITY
You must be at least 18 years old, or have the consent of a parent or guardian, to create an account. Children under 13 are not permitted to use the service.

3. YOUR ACCOUNT
You are responsible for keeping your password confidential and for all activity under your account.

4. CHANGES TO THE SERVICE
We may revise these Terms at any time by posting the updated version on this page, and you are responsible for checking it regularly. Chatterly reserves the right to modify or discontinue the service, its features or its pricing at any time without notice.

5. YOUR CONTENT
5.1 You retain ownership of the content you post and grant us a licence to display it within the service.
5.2 We may remove or disable access to any content that you upload at our sole discretion, without giving any reason.

6. TERMINATION
We may suspend or terminate your account at any time, for any reason or no reason, without notice or liability to you. If your account is terminated, all your data, wallet balance and content may be permanently deleted without any refund.

7. PAYMENTS
7.1 Premium features are available on a monthly subscription that you can cancel at any time.
7.2 Payments are processed by a third-party payment gateway, and we do not store your full card details.

8. DISCLAIMER AND LIMITATION OF LIABILITY
8.1 The service is provided on an "as is" and "as available" basis without warranties of any kind, and you use it at your own risk.
8.2 To the maximum extent permitted by law, Chatterly shall not be liable for any indirect, incidental, special or consequential damages, loss of data or loss of profits. In no event shall our total liability to you exceed Rs. 1,000.

9. GOVERNING LAW AND DISPUTES
9.1 These Terms shall be governed by the laws of the State of Delaware, without regard to its conflict of law provisions.
9.2 All disputes shall be resolved through binding individual arbitration administered by the Singapore International Arbitration Centre, and you waive your right to participate in a class action.
9.3 Any claim against Chatterly must be brought exclusively in the courts located at Singapore.

PRIVACY POLICY

10. INFORMATION WE COLLECT
We collect your name, e-mail address, phone number and the content you share. By using the app you allow us to access your contacts, photos, microphone and location.

11. HOW WE SHARE INFORMATION
11.1 We may share your personal information, including contacts, location and usage data, with our partners, advertisers and affiliates for marketing and other purposes.
11.2 Your data may be transferred to and stored in any country where we or our partners operate and may be retained indefinitely.

12. COOKIES
We use cookies to keep you signed in and to understand how the app is used, and you can manage cookie preferences in Settings.

13. SECURITY
We use industry-standard encryption to protect your data in transit and at rest.

14. YOUR RIGHTS
You can request a copy of your personal data or ask us to correct it by writing to our Grievance Officer at grievance@chatterly.example. Our Grievance Officer will acknowledge complaints within 24 hours and resolve them within 15 days.

15. CONTACT
Chatterly Social Pvt. Ltd., 5th Floor, Orion Business Park, Baner, Pune 411045.
"""

RENTAL_FAIR = """LEAVE AND LICENCE AGREEMENT

This Leave and Licence Agreement is made at Pune on this 10th day of June 2026 between Mrs. Anjali Joshi, residing at 22, Mayur Colony, Kothrud, Pune 411038, hereinafter called the Licensor, and Mr. Kunal Bhide, hereinafter called the Licensee.

1. PREMISES
The Licensor is the absolute owner of Flat No. A-102, Green Valley, Baner, Pune 411045, admeasuring about 650 sq. ft. carpet area, together with the fixtures listed in Annexure I.

2. PERIOD
The licence is granted for a period of 11 (eleven) months commencing from 1 July 2026 and ending on 31 May 2027.

3. LICENCE FEE
3.1 The Licensee shall pay a monthly licence fee of Rs. 16,000 (Rupees Sixteen Thousand only) on or before the 7th day of every English calendar month.
3.2 If the licence is renewed, the licence fee for the next period may be increased by not more than 5% with the mutual written consent of both parties.

4. SECURITY DEPOSIT
4.1 The Licensee has paid an interest-free refundable security deposit of Rs. 32,000 (Rupees Thirty Two Thousand only) to the Licensor.
4.2 The security deposit shall be refunded in full within 15 days of the Licensee handing over vacant possession, after deducting unpaid bills, if any, with a written statement of deductions.

5. NOTICE
Either party may terminate this agreement by giving one month's written notice to the other party.

6. USE OF PREMISES
6.1 The premises shall be used only for residential purposes by the Licensee and the members of the Licensee's family.
6.2 The Licensee shall not sub-let, assign or part with possession of the premises or any part of it.

7. CHARGES
7.1 The Licensee shall pay the electricity and water bills as per the actual consumption recorded on the meter.
7.2 The monthly society maintenance charges and property tax shall be paid by the Licensor.

8. REPAIRS
8.1 The Licensee shall keep the premises clean and in good condition and shall not make any structural alterations without the prior written consent of the Licensor.
8.2 The Licensor shall carry out major repairs such as plumbing, roof leakage and electrical wiring at the Licensor's own cost within a reasonable time.

9. INSPECTION
The Licensor or the Licensor's representative may inspect the premises at a reasonable hour after giving at least 24 hours' prior notice to the Licensee.

10. PEACEFUL USE
The Licensee shall be entitled to peaceful use and enjoyment of the premises during the licence period without interference from the Licensor.

11. HANDOVER
The Licensee shall hand over the premises in the same condition as received, subject to normal wear and tear.

12. REGISTRATION
This agreement shall be registered with the Sub-Registrar, and the stamp duty and registration charges shall be shared equally by both parties.

13. NOTICES
Any notice under this agreement shall be given in writing and delivered by hand, registered post or e-mail to the addresses mentioned above.

14. POLICE VERIFICATION
The Licensee shall submit a copy of identity proof and the police verification form as required by the local police station.

Both parties have read and understood the terms of this agreement and have signed it in the presence of two witnesses.

Licensor: Anjali Joshi            Licensee: Kunal Bhide
"""

OFFER_FAIR = """NIMBUS INFOSOFT PVT. LTD.
4th Floor, Panchshil Tech Park, Yerawada, Pune 411006

Date: 15 June 2026

To,
Mr. Rahul Sawant
Shivaji Nagar, Pune 411005

Subject: Offer of Employment - Software Developer Trainee

Dear Rahul,

1. APPOINTMENT
We are pleased to offer you the position of Software Developer Trainee at Nimbus Infosoft Pvt. Ltd., Pune, with effect from 1 August 2026.

2. COMPENSATION
2.1 Your annual cost to company (CTC) will be Rs. 5,25,000 (Rupees Five Lakh Twenty Five Thousand only), the break-up of which is given in Annexure A.
2.2 Your salary will be credited to your bank account on the last working day of each month after statutory deductions such as income tax and professional tax.
2.3 You will be eligible for an annual performance review, and any increment will be based on your performance and the Company's policy.

3. PROBATION
You will be on probation for a period of six months from the date of joining, after which your performance will be reviewed.

4. TRAINING
You will undergo a classroom training programme for the first eight weeks, and the cost of this training will be borne entirely by the Company.

5. NOTICE PERIOD
Either party may terminate the employment by giving 30 days' written notice or salary in lieu of notice.

6. WORKING HOURS AND LEAVE
6.1 Your normal working hours will be from 9:30 a.m. to 6:30 p.m., Monday to Friday, with a one-hour lunch break.
6.2 You will be entitled to 21 days of paid leave in a calendar year, in addition to the public holidays declared by the Company.
6.3 You will be entitled to maternity or paternity leave as per the Company policy and applicable law.

7. BENEFITS
7.1 You will be covered under the Company's group medical insurance policy for Rs. 5,00,000 for yourself, your spouse and children.
7.2 Provident Fund and gratuity will be applicable as per the provisions of the relevant statutes.
7.3 The Company will reimburse reasonable travel and accommodation expenses incurred for official work as per the travel policy.

8. CONFIDENTIALITY
You shall maintain the confidentiality of all proprietary information of the Company during and after your employment.

9. PERSONAL DATA
Your personal data will be processed only for employment-related purposes and in accordance with applicable data protection law.

10. WORKPLACE
The Company follows a policy of equal opportunity and does not tolerate harassment of any kind at the workplace.

11. VERIFICATION
Your appointment is subject to satisfactory background verification and a medical fitness certificate.

12. ACCEPTANCE
Please sign and return a copy of this letter as a token of your acceptance within seven days of receiving it. This letter, together with its annexures, constitutes the entire terms of your employment with the Company.

We look forward to welcoming you to Nimbus.

For Nimbus Infosoft Pvt. Ltd.
Pooja Kale, HR Manager
"""

SAMPLES = {"rental_agreement": ("Leave and Licence Agreement", RENTAL),
           "offer_letter": ("Offer Letter", OFFER),
           "app_terms": ("Terms of Service", TERMS),
           "rental_agreement_fair": ("Leave and Licence Agreement", RENTAL_FAIR),
           "offer_letter_fair": ("Offer Letter", OFFER_FAIR)}


def to_pdf(path: Path, header: str, text: str) -> None:
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontName="Times-Roman", fontSize=11.5, leading=17, spaceAfter=6)
    head = ParagraphStyle("h", parent=body, fontName="Times-Bold")

    def decorate(canvas, doc):
        # repeated header/footer and page number (the extractor should strip these)
        canvas.saveState()
        canvas.setFont("Times-Italic", 8)
        canvas.drawString(20 * mm, 287 * mm, f"{header} - Confidential")
        canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    story = []
    for para in text.strip().split("\n"):
        para = para.strip()
        if not para:
            story.append(Spacer(1, 4))
            continue
        safe = para.replace("&", "&amp;").replace("<", "&lt;")
        is_head = para.isupper() or (para[:3].strip(". ").isdigit() and para.split(" ", 1)[-1].isupper())
        story.append(Paragraph(safe, head if is_head else body))
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
                      topMargin=22 * mm, bottomMargin=20 * mm).build(story, onFirstPage=decorate, onLaterPages=decorate)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (header, text) in SAMPLES.items():
        (OUT / f"{name}.txt").write_text(text.strip() + "\n", encoding="utf-8")
        to_pdf(OUT / f"{name}.pdf", header, text)
        print(f"wrote {name}.txt and {name}.pdf")


if __name__ == "__main__":
    main()
