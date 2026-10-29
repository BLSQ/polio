import { useApiTeamsDropdownList } from '../../../../../hat/assets/js/apps/Iaso/api/teams';

export const useUserHasTeam = (userId?: number): boolean => {
    const { data } = useApiTeamsDropdownList(
        userId
            ? {
                  users: [userId],
              }
            : {},
        {
            query : {
                enabled: !!userId,
            },
        },
    );
    return !!data?.length;
};
