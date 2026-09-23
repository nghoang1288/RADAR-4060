"""
RADAR-4060: Vietnamese Medical Terminology Mapping for All 146 RADAR Findings.

Provides medically natural Vietnamese translations for all 18 organs/structures
and 146 radiological findings evaluated by RADAR, while retaining English
labels for auditability.
"""

ORGAN_MAPPING_VI = {
    "Aorta": "Động mạch chủ",
    "Duodenum": "Tá tràng",
    "Large bowel": "Đại tràng",
    "Small bowel": "Ruột non",
    "Heart": "Tim & Màng ngoài tim",
    "Rib": "Xương sườn",
    "Liver": "Gan & Đường mật trong gan",
    "Lung": "Phổi & Màng phổi",
    "Kidney": "Thận",
    "Adrenal gland": "Tuyến thượng thận",
    "Stomach": "Dạ dày",
    "Gallbladder": "Túi mật & Đường mật ngoài gan",
    "Pancreas": "Tụy & Quanh tụy",
    "Spleen": "Lách",
    "Bladder": "Bàng quang",
    "Portal vein": "Tĩnh mạch cửa",
    "Esophagus": "Thực quản",
    "Sacrum": "Xương cùng",
    # Chinese organ fallbacks
    "主动脉": "Động mạch chủ",
    "十二指肠": "Tá tràng",
    "大肠": "Đại tràng",
    "小肠": "Ruột non",
    "心脏": "Tim & Màng ngoài tim",
    "肋骨": "Xương sườn",
    "肝": "Gan & Đường mật trong gan",
    "肺": "Phổi & Màng phổi",
    "肾": "Thận",
    "肾上腺": "Tuyến thượng thận",
    "胃": "Dạ dày",
    "胆囊": "Túi mật & Đường mật ngoài gan",
    "胰腺": "Tụy & Quanh tụy",
    "脾": "Lách",
    "膀胱": "Bàng quang",
    "门静脉": "Tĩnh mạch cửa",
    "食管": "Thực quản",
    "骶骨": "Xương cùng",
}

# Complete mapping for all 146 findings keyed by Chinese label and English label
FINDING_MAPPING_VI = {
    # --- Động mạch chủ (Aorta) ---
    "主动脉_主动脉夹层": "Bóc tách động mạch chủ",
    "Aorta_Aortic dissection": "Bóc tách động mạch chủ",
    "主动脉_主动脉瘤": "Phình động mạch chủ",
    "Aorta_Aortic aneurysm": "Phình động mạch chủ",
    "主动脉_粥样硬化": "Xơ vữa động mạch chủ",
    "Aorta_Atherosclerosis": "Xơ vữa động mạch chủ",
    "主动脉_钙化": "Vôi hóa động mạch chủ",
    "Aorta_Calcification": "Vôi hóa động mạch chủ",

    # --- Tá tràng (Duodenum) ---
    "十二指肠_占位": "Tổn thương choán chỗ tá tràng",
    "Duodenum_Mass": "Tổn thương choán chỗ tá tràng",
    "十二指肠_囊袋状突出影": "Hình túi lồi dạng túi tá tràng",
    "Duodenum_Saccular outpouching": "Hình túi lồi dạng túi tá tràng",
    "十二指肠_憩室": "Túi thừa tá tràng",
    "Duodenum_Diverticulum": "Túi thừa tá tràng",
    "十二指肠_梗阻": "Tắc tá tràng",
    "Duodenum_Obstruction": "Tắc tá tràng",
    "十二指肠_溃疡": "Loét tá tràng",
    "Duodenum_Ulcer": "Loét tá tràng",

    # --- Đại tràng (Large bowel) ---
    "大肠_克罗恩病": "Bệnh Crohn đại tràng",
    "Large bowel_Crohn's disease": "Bệnh Crohn đại tràng",
    "大肠_大肠（壁）钙化": "Vôi hóa thành đại tràng",
    "Large bowel_Mural calcification": "Vôi hóa thành đại tràng",
    "大肠_急慢性（结）肠炎": "Viêm đại tràng cấp/mạn",
    "Large bowel_Colitis": "Viêm đại tràng cấp/mạn",
    "大肠_浆膜面毛糙": "Thanh mạc đại tràng thô nham nhở",
    "Large bowel_Serosal surface irregularity": "Thanh mạc đại tràng thô nham nhở",
    "大肠_溃疡性结肠炎": "Viêm loét đại tràng (UC)",
    "Large bowel_Ulcerative colitis": "Viêm loét đại tràng (UC)",
    "大肠_直肠癌": "Ung thư trực tràng",
    "Large bowel_Rectal cancer": "Ung thư trực tràng",
    "大肠_积液积气": "Ứ dịch / ứ khí đại tràng",
    "Large bowel_Gas and fluid accumulation": "Ứ dịch / ứ khí đại tràng",
    "大肠_结肠癌": "Ung thư đại tràng",
    "Large bowel_Colon cancer": "Ung thư đại tràng",
    "大肠_肠壁毛糙": "Thành đại tràng không đều nham nhở",
    "Large bowel_Wall irregularity": "Thành đại tràng không đều nham nhở",
    "大肠_肠壁水肿": "Phù nề thành đại tràng",
    "Large bowel_Wall edema": "Phù nề thành đại tràng",
    "大肠_肠套叠": "Lồng ruột đại tràng",
    "Large bowel_Intussusception": "Lồng ruột đại tràng",
    "大肠_肠憩室": "Túi thừa đại tràng",
    "Large bowel_Diverticulum": "Túi thừa đại tràng",
    "大肠_肠梗阻": "Tắc đại tràng",
    "Large bowel_Obstruction": "Tắc đại tràng",
    "大肠_肠穿孔": "Thủng đại tràng",
    "Large bowel_Perforation": "Thủng đại tràng",
    "大肠_肠道扩张": "Giãn đại tràng",
    "Large bowel_Dilatation": "Giãn đại tràng",
    "大肠_脂肪间隙模糊": "Thâm nhiễm mỡ quanh đại tràng",
    "Large bowel_Blurring of fat planes": "Thâm nhiễm mỡ quanh đại tràng",
    "大肠_阑尾炎": "Viêm ruột thừa",
    "Large bowel_Appendicitis": "Viêm ruột thừa",
    "大肠_阑尾粪石": "Sỏi phân ruột thừa",
    "Large bowel_Appendicolith": "Sỏi phân ruột thừa",

    # --- Ruột non (Small bowel) ---
    "小肠_克罗恩病": "Bệnh Crohn ruột non",
    "Small bowel_Crohn's disease": "Bệnh Crohn ruột non",
    "小肠_套叠": "Lồng ruột non",
    "Small bowel_Intussusception": "Lồng ruột non",
    "小肠_扭转": "Xoắn ruột non",
    "Small bowel_Volvulus": "Xoắn ruột non",
    "小肠_梗阻": "Tắc ruột non",
    "Small bowel_Obstruction": "Tắc ruột non",
    "小肠_淋巴瘤": "U lympho ruột non",
    "Small bowel_Lymphoma": "U lympho ruột non",
    "小肠_积气积液": "Ứ dịch / ứ khí ruột non",
    "Small bowel_Gas and fluid accumulation": "Ứ dịch / ứ khí ruột non",
    "小肠_系膜指膜炎": "Viêm mạc treo ruột (Panniculitis)",
    "Small bowel_Mesenteric panniculitis": "Viêm mạc treo ruột (Panniculitis)",
    "小肠_系膜淋巴结肿大": "Hạch mạc treo ruột phì đại",
    "Small bowel_Mesenteric lymphadenopathy": "Hạch mạc treo ruột phì đại",
    "小肠_肠壁增厚": "Dày thành ruột non",
    "Small bowel_Wall thickening": "Dày thành ruột non",
    "小肠_肠管扩张": "Giãn quai ruột non",
    "Small bowel_Dilatation": "Giãn quai ruột non",
    "小肠_脂肪瘤": "U mỡ ruột non",
    "Small bowel_Lipoma": "U mỡ ruột non",
    "小肠_间质瘤（胃肠间质瘤-gist）": "U mô đệm đường tiêu hóa ruột non (GIST)",
    "Small bowel_Gastrointestinal stromal tumor": "U mô đệm đường tiêu hóa ruột non (GIST)",
    "小肠_（急慢性）小肠炎": "Viêm ruột non cấp/mạn",
    "Small bowel_Enteritis": "Viêm ruột non cấp/mạn",

    # --- Tim & Màng ngoài tim (Heart) ---
    "心脏_心包积液": "Tràn dịch màng ngoài tim",
    "Heart_Pericardial effusion": "Tràn dịch màng ngoài tim",
    "心脏_心影（脏）增大": "Bóng tim to / Tim to",
    "Heart_Cardiomegaly": "Bóng tim to / Tim to",

    # --- Xương sườn (Rib) ---
    "肋骨_转移瘤（乳腺癌 骨转移）": "Di căn xương sườn",
    "Rib_Metastasis": "Di căn xương sườn",
    "肋骨_骨折": "Gãy xương sườn",
    "Rib_Fracture": "Gãy xương sườn",
    "肋骨_骨质破坏": "Tiêu hủy / phá hủy xương sườn",
    "Rib_Bone destruction": "Tiêu hủy / phá hủy xương sườn",

    # --- Gan & Đường mật trong gan (Liver) ---
    "肝_低密度影": "Tổn thương giảm tỷ trọng gan",
    "Liver_Hypoattenuating lesion": "Tổn thương giảm tỷ trọng gan",
    "肝_格林森鞘积液": "Phù nề quanh khoảng cửa (khoang Glisson)",
    "Liver_Periportal edema": "Phù nề quanh khoảng cửa (khoang Glisson)",
    "肝_比例失调": "Mất cân đối tỷ lệ thể tích thùy gan",
    "Liver_Lobar volume disproportion": "Mất cân đối tỷ lệ thể tích thùy gan",
    "肝_波浪状改变": "Bờ gan dạng lượn sóng",
    "Liver_Undulating contour": "Bờ gan dạng lượn sóng",
    "肝_硬化": "Xơ gan",
    "Liver_Cirrhosis": "Xơ gan",
    "肝_结节状强化": "Ngấm thuốc dạng nốt nhu mô gan",
    "Liver_Nodular enhancement": "Ngấm thuốc dạng nốt nhu mô gan",
    "肝_肝内胆管扩张": "Giãn đường mật trong gan",
    "Liver_Intrahepatic bile duct dilatation": "Giãn đường mật trong gan",
    "肝_肝内胆管结石": "Sỏi đường mật trong gan",
    "Liver_Hepatolithiasis": "Sỏi đường mật trong gan",
    "肝_肝内钙化灶": "Nốt vôi hóa trong gan",
    "Liver_Intrahepatic calcification": "Nốt vôi hóa trong gan",
    "肝_肝囊肿": "Nang gan",
    "Liver_Cyst": "Nang gan",
    "肝_肝细胞癌": "Ung thư biểu mô tế bào gan (HCC)",
    "Liver_Hepatocellular carcinoma": "Ung thư biểu mô tế bào gan (HCC)",
    "肝_肝胆管内高密度影": "Tăng tỷ trọng trong đường mật gan",
    "Liver_Hyperattenuating lesion in intrahepatic bile ducts": "Tăng tỷ trọng trong đường mật gan",
    "肝_肝血管瘤": "U mạch máu gan (Hemangioma)",
    "Liver_Hemangioma": "U mạch máu gan (Hemangioma)",
    "肝_胆管癌": "Ung thư đường mật trong gan",
    "Liver_Intrahepatic cholangiocarcinoma": "Ung thư đường mật trong gan",
    "肝_脂肪肝": "Thoái hóa mỡ gan (Gan nhiễm mỡ)",
    "Liver_Steatotic liver disease": "Thoái hóa mỡ gan (Gan nhiễm mỡ)",
    "肝_脓肿": "Áp xe gan",
    "Liver_Abscess": "Áp xe gan",
    "肝_转移瘤": "U gan di căn",
    "Liver_Metastasis": "U gan di căn",
    "肝_边缘不规则": "Bờ gan không đều nham nhở",
    "Liver_Irregular margin": "Bờ gan không đều nham nhở",

    # --- Phổi & Màng phổi (Lung) ---
    "肺_斑片影": "Đám mờ dạng mảng phổi",
    "Lung_Patchy opacity": "Đám mờ dạng mảng phổi",
    "肺_气胸": "Tràn khí màng phổi",
    "Lung_Pneumothorax": "Tràn khí màng phổi",
    "肺_结节": "Nốt mờ phổi",
    "Lung_Nodule": "Nốt mờ phổi",
    "肺_肺占位": "Khối choán chỗ phổi",
    "Lung_Mass": "Khối choán chỗ phổi",
    "肺_肺萎陷": "Xẹp phổi hoàn toàn",
    "Lung_Pulmonary collapse": "Xẹp phổi hoàn toàn",
    "肺_胸腔积液": "Tràn dịch màng phổi",
    "Lung_Pleural effusion": "Tràn dịch màng phổi",
    "肺_膨胀不全": "Xẹp phổi / Giãn nở không hoàn toàn",
    "Lung_Atelectasis": "Xẹp phổi / Giãn nở không hoàn toàn",
    "肺_转移瘤": "U phổi di căn",
    "Lung_Metastasis": "U phổi di căn",
    "肺_钙化灶": "Nốt vôi hóa phổi",
    "Lung_Calcification": "Nốt vôi hóa phổi",
    "肺_高密度影": "Đám tăng tỷ trọng phổi",
    "Lung_Hyperattenuating opacity": "Đám tăng tỷ trọng phổi",

    # --- Thận (Kidney) ---
    "肾_低密度影": "Tổn thương giảm tỷ trọng thận",
    "Kidney_Hypoattenuating lesion": "Tổn thương giảm tỷ trọng thận",
    "肾_囊肿": "Nang thận",
    "Kidney_Cyst": "Nang thận",
    "肾_多囊肾": "Thận đa nang",
    "Kidney_Polycystic kidney disease": "Thận đa nang",
    "肾_实质变薄": "Nhu mô thận mỏng",
    "Kidney_Parenchymal thinning": "Nhu mô thận mỏng",
    "肾_无强化囊性灶": "Tổn thương dạng nang không ngấm thuốc",
    "Kidney_Nonenhancing cystic lesion": "Tổn thương dạng nang không ngấm thuốc",
    "肾_肾动脉瘤": "Phình động mạch thận",
    "Kidney_Renal artery aneurysm": "Phình động mạch thận",
    "肾_肾盂扩张": "Giãn bể thận",
    "Kidney_Renal pelvic dilatation": "Giãn bể thận",
    "肾_肾盂癌": "Ung thư bể thận",
    "Kidney_Renal pelvic cancer": "Ung thư bể thận",
    "肾_肾盂积水": "Thận ứ nước",
    "Kidney_Hydronephrosis": "Thận ứ nước",
    "肾_肾细胞癌（透明细胞癌）": "Ung thư biểu mô tế bào thận (RCC)",
    "Kidney_Renal cell carcinoma": "Ung thư biểu mô tế bào thận (RCC)",
    "肾_肾萎缩": "Teo thận",
    "Kidney_Atrophy": "Teo thận",
    "肾_肾血管平滑肌脂肪瘤": "U cơ mỡ mạch thận (AML)",
    "Kidney_Angiomyolipoma": "U cơ mỡ mạch thận (AML)",
    "肾_肾（盂）结石": "Sỏi thận / sỏi bể thận",
    "Kidney_Nephrolithiasis": "Sỏi thận / sỏi bể thận",
    "肾_高密度影": "Nốt tăng tỷ trọng thận",
    "Kidney_Hyperattenuating lesion": "Nốt tăng tỷ trọng thận",

    # --- Tuyến thượng thận (Adrenal gland) ---
    "肾上腺_增生": "Tăng sản tuyến thượng thận",
    "Adrenal gland_Hyperplasia": "Tăng sản tuyến thượng thận",
    "肾上腺_结节": "Nốt tuyến thượng thận",
    "Adrenal gland_Nodule": "Nốt tuyến thượng thận",
    "肾上腺_脂肪瘤": "U mỡ tuyến thượng thận",
    "Adrenal gland_Lipoma": "U mỡ tuyến thượng thận",
    "肾上腺_腺瘤": "U tuyến thượng thận (Adenoma)",
    "Adrenal gland_Adenoma": "U tuyến thượng thận (Adenoma)",
    "肾上腺_转移瘤": "Di căn tuyến thượng thận",
    "Adrenal gland_Metastasis": "Di căn tuyến thượng thận",
    "肾上腺_钙化": "Vôi hóa tuyến thượng thận",
    "Adrenal gland_Calcification": "Vôi hóa tuyến thượng thận",

    # --- Dạ dày (Stomach) ---
    "胃_壁水肿": "Phù nề thành dạ dày",
    "Stomach_Wall edema": "Phù nề thành dạ dày",
    "胃_扩张": "Giãn dạ dày",
    "Stomach_Dilatation": "Giãn dạ dày",
    "胃_胃底静脉曲张": "Giãn tĩnh mạch phình vị dạ dày",
    "Stomach_Gastric fundal varices": "Giãn tĩnh mạch phình vị dạ dày",
    "胃_胃溃疡": "Loét dạ dày",
    "Stomach_Ulcer": "Loét dạ dày",
    "胃_胃癌": "Ung thư dạ dày",
    "Stomach_Gastric cancer": "Ung thư dạ dày",
    "胃_间质瘤（gist）": "U mô đệm đường tiêu hóa dạ dày (GIST)",
    "Stomach_Gastrointestinal stromal tumor (GIST)": "U mô đệm đường tiêu hóa dạ dày (GIST)",

    # --- Túi mật & Đường mật ngoài gan (Gallbladder) ---
    "胆囊_结石": "Sỏi túi mật",
    "Gallbladder_Cholecystolithiasis": "Sỏi túi mật",
    "胆囊_结节状致密影": "Nốt tăng tỷ trọng dạng sỏi túi mật",
    "Gallbladder_Nodular stone-like hyperattenuating lesion": "Nốt tăng tỷ trọng dạng sỏi túi mật",
    "胆囊_胆囊增大": "Túi mật căng to",
    "Gallbladder_Distention": "Túi mật căng to",
    "胆囊_胆囊炎": "Viêm túi mật",
    "Gallbladder_Cholecystitis": "Viêm túi mật",
    "胆囊_胆囊癌": "Ung thư túi mật",
    "Gallbladder_Gallbladder cancer": "Ung thư túi mật",
    "胆囊_胆囊腺肌症": "U cơ tuyến túi mật (Adenomyomatosis)",
    "Gallbladder_Adenomyomatosis": "U cơ tuyến túi mật (Adenomyomatosis)",
    "胆囊_胆管壁增厚": "Dày thành đường mật ngoài gan",
    "Gallbladder_Extrahepatic bile duct wall thickening": "Dày thành đường mật ngoài gan",
    "胆囊_胆管扩张": "Giãn đường mật ngoài gan",
    "Gallbladder_Extrahepatic bile duct dilatation": "Giãn đường mật ngoài gan",
    "胆囊_胆管炎": "Viêm đường mật ngoài gan",
    "Gallbladder_Cholangitis": "Viêm đường mật ngoài gan",
    "胆囊_胆管癌": "Ung thư đường mật ngoài gan",
    "Gallbladder_Cholangiocarcinoma": "Ung thư đường mật ngoài gan",
    "胆囊_胆管积气": "Khí trong đường mật ngoài gan",
    "Gallbladder_Pneumobilia": "Khí trong đường mật ngoài gan",
    "胆囊_胆管结石": "Sỏi đường mật ngoài gan",
    "Gallbladder_Extrahepatic bile duct stone": "Sỏi đường mật ngoài gan",
    "胆囊_高密度影": "Đám tăng tỷ trọng túi mật/đường mật",
    "Gallbladder_Hyperattenuating lesion": "Đám tăng tỷ trọng túi mật/đường mật",
    "胆囊_黄色肉芽肿": "Viêm túi mật u hạt vàng",
    "Gallbladder_Xanthogranuloma": "Viêm túi mật u hạt vàng",

    # --- Tụy & Quanh tụy (Pancreas) ---
    "胰腺_低密度影": "Tổn thương giảm tỷ trọng tụy",
    "Pancreas_Low-density lesion": "Tổn thương giảm tỷ trọng tụy",
    "胰腺_囊肿": "Nang tụy",
    "Pancreas_Cyst": "Nang tụy",
    "胰腺_围脂肪间隙模糊": "Thâm nhiễm mỡ quanh tụy",
    "Pancreas_Blurring of peripancreatic fat planes": "Thâm nhiễm mỡ quanh tụy",
    "胰腺_肿瘤或胰腺癌": "U tụy / Ung thư tụy",
    "Pancreas_Pancreatic cancer": "U tụy / Ung thư tụy",
    "胰腺_胰周假性囊肿": "Nang giả tụy quanh tụy",
    "Pancreas_Peripancreatic pseudocyst": "Nang giả tụy quanh tụy",
    "胰腺_胰管扩张": "Giãn ống tụy chính",
    "Pancreas_Pancreatic duct dilatation": "Giãn ống tụy chính",
    "胰腺_胰管结石": "Sỏi ống tụy",
    "Pancreas_Pancreatic duct calculus": "Sỏi ống tụy",
    "胰腺_胰腺炎": "Viêm tụy",
    "Pancreas_Pancreatitis": "Viêm tụy",
    "胰腺_胰腺饱满": "Tụy phì đại / Căng đầy",
    "Pancreas_Enlargement": "Tụy phì đại / Căng đầy",
    "胰腺_萎缩": "Teo nhu mô tụy",
    "Pancreas_Atrophy": "Teo nhu mô tụy",

    # --- Lách (Spleen) ---
    "脾_低密度灶": "Tổn thương giảm tỷ trọng lách",
    "Spleen_Hypoattenuating lesion": "Tổn thương giảm tỷ trọng lách",
    "脾_副脾": "Lách phụ",
    "Spleen_Accessory spleen": "Lách phụ",
    "脾_囊肿": "Nang lách",
    "Spleen_Cyst": "Nang lách",
    "脾_梗死": "Nhồi máu lách",
    "Spleen_Infarction": "Nhồi máu lách",
    "脾_片状低密度区": "Vùng giảm tỷ trọng dạng mảng lách",
    "Spleen_Patchy hypoattenuating lesion": "Vùng giảm tỷ trọng dạng mảng lách",
    "脾_脾大": "Lách to",
    "Spleen_Splenomegaly": "Lách to",
    "脾_脾脏淋巴瘤": "U lympho lách",
    "Spleen_Lymphoma": "U lympho lách",
    "脾_钙化": "Nốt vôi hóa lách",
    "Spleen_Calcification": "Nốt vôi hóa lách",

    # --- Bàng quang (Bladder) ---
    "膀胱_憩室": "Túi thừa bàng quang",
    "Bladder_Diverticulum": "Túi thừa bàng quang",
    "膀胱_结石": "Sỏi bàng quang",
    "Bladder_Stone": "Sỏi bàng quang",
    "膀胱_膀胱壁毛糙": "Thành bàng quang dày không đều",
    "Bladder_Wall irregularity": "Thành bàng quang dày không đều",
    "膀胱_膀胱炎": "Viêm bàng quang",
    "Bladder_Cystitis": "Viêm bàng quang",
    "膀胱_膀胱癌": "Ung thư bàng quang",
    "Bladder_Bladder cancer": "Ung thư bàng quang",
    "膀胱_软组织密度影": "Tổn thương tỷ trọng mô mềm bàng quang",
    "Bladder_Soft-tissue attenuation lesion": "Tổn thương tỷ trọng mô mềm bàng quang",

    # --- Tĩnh mạch cửa (Portal vein) ---
    "门静脉_增宽": "Giãn tĩnh mạch cửa",
    "Portal vein_Dilatation": "Giãn tĩnh mạch cửa",
    "门静脉_栓塞": "Huyết khối tĩnh mạch cửa",
    "Portal vein_Thrombosis": "Huyết khối tĩnh mạch cửa",
    "门静脉_高压": "Tăng áp lực tĩnh mạch cửa",
    "Portal vein_Hypertension": "Tăng áp lực tĩnh mạch cửa",

    # --- Thực quản (Esophagus) ---
    "食管_增粗迂曲血管影": "Mạch máu thực quản giãn ngoằn ngoèo",
    "Esophagus_Dilated and tortuous tubular opacities": "Mạch máu thực quản giãn ngoằn ngoèo",
    "食管_管壁增厚": "Dày thành thực quản",
    "Esophagus_Wall thickening": "Dày thành thực quản",
    "食管_裂孔疝": "Thoát vị hoành (Hiatal hernia)",
    "Esophagus_Hiatal hernia": "Thoát vị hoành (Hiatal hernia)",
    "食管_静脉扩张迂曲": "Tĩnh mạch thực quản giãn ngoằn ngoèo",
    "Esophagus_Dilated and tortuous veins": "Tĩnh mạch thực quản giãn ngoằn ngoèo",
    "食管_静脉曲张": "Giãn tĩnh mạch thực quản",
    "Esophagus_Varices": "Giãn tĩnh mạch thực quản",

    # --- Xương cùng (Sacrum) ---
    "骶骨_骨炎": "Viêm xương cùng",
    "Sacrum_Osteitis": "Viêm xương cùng",
}


def parse_finding_label(column_header: str) -> dict:
    """
    Parse a RADAR CSV column header, e.g.
    '主动脉_钙化 (Aorta_Calcification)' or 'Aorta_Calcification' or '主动脉_钙化'
    Returns dict:
      organ_vi: Vietnamese organ name
      finding_vi: Vietnamese finding description
      organ_en: English organ name
      finding_en: English finding description
      full_en: English key
      full_cn: Chinese key
    """
    raw = column_header.strip()
    cn_part = ""
    en_part = ""

    if "(" in raw and raw.endswith(")"):
        cn_part = raw[: raw.find("(")].strip()
        en_part = raw[raw.find("(") + 1 : -1].strip()
    elif "_" in raw:
        # Check if english or chinese
        first = raw.split("_")[0]
        if first in ORGAN_MAPPING_VI:
            if any(ord(c) > 127 for c in first):
                cn_part = raw
            else:
                en_part = raw

    organ_en = en_part.split("_")[0] if "_" in en_part else ""
    finding_en = en_part.split("_", 1)[1] if "_" in en_part else en_part

    organ_cn = cn_part.split("_")[0] if "_" in cn_part else ""
    finding_cn = cn_part.split("_", 1)[1] if "_" in cn_part else cn_part

    # Lookup Vietnamese organ
    organ_vi = ORGAN_MAPPING_VI.get(organ_en) or ORGAN_MAPPING_VI.get(organ_cn) or organ_en or organ_cn or "Cơ quan khác"

    # Lookup Vietnamese finding
    finding_vi = (
        FINDING_MAPPING_VI.get(cn_part)
        or FINDING_MAPPING_VI.get(en_part)
        or FINDING_MAPPING_VI.get(raw)
        or finding_en
        or finding_cn
        or raw
    )

    return {
        "organ_vi": organ_vi,
        "finding_vi": finding_vi,
        "organ_en": organ_en,
        "finding_en": finding_en,
        "full_en": en_part or raw,
        "full_cn": cn_part or raw,
        "raw_column": raw,
    }
