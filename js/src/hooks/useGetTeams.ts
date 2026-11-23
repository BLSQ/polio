import { useApiTeamsDropdownList } from 'Iaso/api/teams/endpoints/teams/teams';

export const useUserHasTeam = (userId?: number): boolean => {
    const { data } = useApiTeamsDropdownList(
        userId
            ? {
                  users: [userId],
              }
            : {},
        {
            query: {
                enabled: !!userId,
            },
        },
    );
    return !!data?.length;
};
