"""
RADAR-4060: Anatomical Coverage Matrix for Abdominal CT Reporting.

Defines the explicit boundary between what RADAR-146 actually evaluates
vs unrepresented abdominal structures (docs/CLINICAL_AUDIT_V3.md Section G).
Prevents unsupported auto-generated normal statements.
"""

COVERAGE_STATUS_SUPPORTED = "Được hỗ trợ đầy đủ bởi RADAR-146"
COVERAGE_STATUS_PARTIAL = "Được hỗ trợ một phần (giới hạn một số tổn thương)"
COVERAGE_STATUS_UNSUPPORTED = "Không thuộc phạm vi khảo sát của RADAR-146"

ANATOMICAL_COVERAGE_MATRIX = [
    {
        "structure": "Gan (Nhu mô & mạch máu trong gan)",
        "organ_en": "Liver",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 19,
        "description": "Bao phủ u gan (HCC, di căn, u mạch), nang, áp xe, xơ gan, vôi hóa, giãn đường mật trong gan.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Tĩnh mạch cửa (Portal vein)",
        "organ_en": "Portal vein",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 3,
        "description": "Bao phủ huyết khối tĩnh mạch cửa, giãn tĩnh mạch cửa, tăng áp lực tĩnh mạch cửa.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Túi mật & Đường mật ngoài gan",
        "organ_en": "Gallbladder",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 14,
        "description": "Bao phủ sỏi túi mật, viêm túi mật, u túi mật, u cơ tuyến (adenomyomatosis), giãn đường mật ngoài gan.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Tụy & Quanh tụy",
        "organ_en": "Pancreas",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 10,
        "description": "Bao phủ viêm tụy cấp/mạn, u tụy/ung thư tụy, nang tụy, sỏi ống tụy, giãn ống tụy.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Lách (Spleen)",
        "organ_en": "Spleen",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 8,
        "description": "Bao phủ lách to, nang lách, nhồi máu lách, u lách / lymphoma, vôi hóa lách.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Tuyến thượng thận 2 bên",
        "organ_en": "Adrenal gland",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 6,
        "description": "Bao phủ tăng sản, nốt tuyến thượng thận, u mỡ, adenoma, u di căn, vôi hóa.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Thận & Bể thận 2 bên",
        "organ_en": "Kidney",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 14,
        "description": "Bao phủ giãn bể thận, thận ứ nước, sỏi thận/bể thận, u thận (RCC, angiomyolipoma), nang thận, teo thận.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Ống tiêu hóa (Dạ dày, Tá tràng, Ruột non, Đại trực tràng)",
        "organ_en": "GI tract",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 42,
        "description": "Bao phủ viêm loét, tắc ruột, thủng ruột, lồng ruột, túi thừa, u đường tiêu hóa, viêm mạc treo.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Động mạch chủ bụng & mạch máu lớn",
        "organ_en": "Aorta",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 4,
        "description": "Bao phủ bóc tách ĐM chủ, phình ĐM chủ, xơ vữa ĐM chủ, vôi hóa thành ĐM chủ.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Bàng quang",
        "organ_en": "Bladder",
        "status": COVERAGE_STATUS_SUPPORTED,
        "radar_findings_count": 6,
        "description": "Bao phủ sỏi bàng quang, viêm bàng quang, u/ung thư bàng quang, túi thừa bàng quang.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Phổi đáy & Màng phổi 2 bên",
        "organ_en": "Lung",
        "status": COVERAGE_STATUS_PARTIAL,
        "radar_findings_count": 10,
        "description": "Chỉ khảo sát phần phổi nằm trong trường chụp bụng (tràn dịch màng phổi, đám mờ, nốt/u phổi đáy). Không thay thế CT ngực.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Khung xương (Xương sườn, Xương cùng)",
        "organ_en": "Bone",
        "status": COVERAGE_STATUS_PARTIAL,
        "radar_findings_count": 4,
        "description": "Chỉ có nhãn gãy xương sườn, tiêu xương sườn, di căn xương sườn và viêm xương cùng. Không đánh giá cột sống, xương chậu.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Dịch tự do ổ bụng / Khoang màng bụng",
        "organ_en": "Peritoneum",
        "status": COVERAGE_STATUS_UNSUPPORTED,
        "radar_findings_count": 0,
        "description": "RADAR-146 KHÔNG có nhãn nhận diện dịch tự do ổ bụng (ascites) hay dịch màng bụng. Cần Bác sĩ tự đánh giá.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Niệu quản 2 bên",
        "organ_en": "Ureter",
        "status": COVERAGE_STATUS_UNSUPPORTED,
        "radar_findings_count": 0,
        "description": "RADAR-146 KHÔNG có nhãn sỏi niệu quản hay dày thành niệu quản. Cần Bác sĩ tự rà soát dọc đường đi niệu quản.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Cơ quan sinh dục tiểu khung (Tử cung, Buồng trứng, Tuyến tiền liệt)",
        "organ_en": "Pelvis",
        "status": COVERAGE_STATUS_UNSUPPORTED,
        "radar_findings_count": 0,
        "description": "RADAR-146 KHÔNG có nhãn u xơ tử cung, nang buồng trứng hay u xơ tiền liệt tuyến.",
        "normal_statement_permitted": False,
    },
    {
        "structure": "Hạch ổ bụng & Sau phúc mạc tổng quát",
        "organ_en": "Lymph nodes",
        "status": COVERAGE_STATUS_UNSUPPORTED,
        "radar_findings_count": 0,
        "description": "Chỉ có hạch mạc treo ruột non; KHÔNG có nhãn hạch sau phúc mạc, hạch cạnh ĐM chủ, hay hạch chậu.",
        "normal_statement_permitted": False,
    },
]


def can_write_normal_statement(organ_name: str) -> bool:
    """Strictly returns False for all structures per docs/CLINICAL_AUDIT_V3.md Section G."""
    return False
