# Self-recorded benchmark prompts

This file contains **prompts only**, not audio or pre-filled performance results. Record them with your own voice or consented volunteers. Save exact ground truth in a UTF-8 file. Never use real account numbers, personal phone numbers or confidential customer audio.

## Hindi/Hinglish prompts
1. मुझे कल सुबह दस बजे कॉल करना है।
2. Mera recharge teen sau ninyaanve rupaye ka tha, but service nahi chal rahi.
3. Bhai electricity bill five hundred forty rupees hai, payment confirm kar do.
4. मेरी ट्रेन रात नौ बजकर पंद्रह मिनट पर आएगी।
5. Sir delivery address change karo, new pin code six zero zero zero one five.

## Tamil/Tanglish prompts
6. நாளை காலை பத்து மணிக்கு எனக்கு reminder வேண்டும்.
7. Anna booking confirm pannunga, appointment evening five thirty ku.
8. இந்த மாதம் நான் ஆயிரத்து ஐநூறு ரூபாய் செலுத்தினேன்.
9. My parcel innum varala, tracking status check pannunga.
10. இந்த சத்தத்தில் உங்களுக்கு என் குரல் கேட்கிறதா?

## Kannada/Kanglish prompts
11. ನಾಳೆ ಬೆಳಗ್ಗೆ ಹತ್ತು ಗಂಟೆಗೆ ನನಗೆ ಕರೆ ಮಾಡಿ.
12. Sir booking confirmation WhatsApp ge kalisi.
13. ವಿದ್ಯುತ್ ಬಿಲ್ ಇನ್ನೂ ಪಾವತಿಯಾಗಿಲ್ಲ.
14. Delivery swalpa delay aagide, tomorrow morning check maadi.
15. ಇಲ್ಲಿ ತುಂಬಾ ಟ್ರಾಫಿಕ್ ಶಬ್ದ ಇದೆ.

## Bengali/Benglish prompts
16. আগামীকাল সকাল দশটায় আমাকে ফোন করবেন।
17. Order ta ekhono asheni, please tracking check korun.
18. আমার বিল পাঁচশো টাকা এসেছে।
19. আজ খুব আওয়াজ হচ্ছে, একটু আস্তে বলুন।
20. Payment successful hoyeche ki? Please confirm korun.

## Dataset protocol
- Record the prompts **naturally**; the mixed-script prompts are suggestions, not canonical ground truth. For each recording, write exactly what was actually spoken.
- Capture a second set of **consented, truly noisy recordings** outside (traffic / cafeteria / station) and keep it separate from artificial mixtures.
- Keep participant counts, conditions, languages, file hash, reference transcript, API model/version, timestamp, seed, SNR and phonetic disagreements in a CSV.
- Separate a development subset from a blind evaluation subset; do not tune noise-recovery parameters on the blind set.
- At least 3 different speakers if possible, varied accents. No claim of statistical significance from small samples.
- Cross-script WER is not a fair comparison if the model transliterates; agree on transcript conventions first.
