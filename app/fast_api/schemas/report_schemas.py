from pydantic import BaseModel
from typing import List


class TeamInfo(BaseModel):
    term: int
    number: int
    receivedPumatiCount: int
    givedPumatiCount: int
    totalBadgeCount: int


class BadgeStat(BaseModel):
    giverTerm: int #팀 기수: 2
    giverTeamNumber: int # 뱃지를 준 팀의 팀 번호
    badgeCount: int # 뱃지를 준 횟수


class DailyPumatiStat(BaseModel):
    day: str  # e.g. "MON", "TUE"
    givedPumatiCount: int 
    receivedPumatiCount: int


class ProjectStatsPayload(BaseModel):
    projectId: int
    projectTitle: str
    team: TeamInfo
    badgeStats: List[BadgeStat]
    dailyPumatiStats: List[DailyPumatiStat]
