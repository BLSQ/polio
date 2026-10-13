import React, { FunctionComponent } from 'react';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
    AlertModal,
    IconButton,
    LoadingSpinner,
    makeFullModal,
    useSafeIntl,
} from 'bluesquare-components';
import { defineMessages } from 'react-intl';

import { Task } from '../../../../../../hat/assets/js/apps/Iaso/domains/tasks/types';
import { userHasPermission } from '../../../../../../hat/assets/js/apps/Iaso/domains/users/utils';
import { getRequest } from '../../../../../../hat/assets/js/apps/Iaso/libs/Api';
import { useSnackQuery } from '../../../../../../hat/assets/js/apps/Iaso/libs/apiHooks';
import { useCurrentUser } from '../../../../../../hat/assets/js/apps/Iaso/utils/usersUtils';

import { NOTIFICATION } from '../../constants/permissions';

const MESSAGES = defineMessages({
    details: {
        defaultMessage: 'Polio Notifications Import Details',
        id: 'iaso.tasks.polioNotificationImport.details',
    },
    errors: {
        defaultMessage:
            "{count} error(s). The following data couldn't be imported.",
        id: 'iaso.tasks.polioNotificationImport.errors',
    },
});

type NotificationImport = {
    id: number;
    errors: unknown[];
};

const useGetPolioNotificationImport = (taskId: number, enabled: boolean) =>
    useSnackQuery<NotificationImport>({
        queryKey: ['polio', 'notification-import', 'task', taskId],
        queryFn: () =>
            getRequest(`/api/polio/notifications/for_task/${taskId}/`),
        options: {
            enabled,
            retry: false,
        },
    });

const resultMessage = (result: Task<unknown>['result']): string | undefined => {
    if (typeof result === 'string') {
        return result;
    }
    if (result && typeof result === 'object' && 'message' in result) {
        const message = (result as { message?: unknown }).message;
        return typeof message === 'string' ? message : undefined;
    }
    return undefined;
};

type ModalProps = {
    task: Task<unknown>;
    isOpen: boolean;
    closeDialog: () => void;
};

const NotificationImportDetailModal: FunctionComponent<ModalProps> = ({
    task,
    isOpen,
    closeDialog,
}) => {
    const { formatMessage } = useSafeIntl();
    const { data: notificationImport, isFetching } =
        useGetPolioNotificationImport(task.id, isOpen);

    return (
        <AlertModal
            isOpen={isOpen}
            closeDialog={closeDialog}
            titleMessage={formatMessage(MESSAGES.details)}
            id="polio-notifications-import-details-modal"
            maxWidth="md"
        >
            {isFetching && <LoadingSpinner />}
            {!isFetching && (
                <>
                    <p>{resultMessage(task.result)}</p>
                    {notificationImport &&
                        notificationImport.errors.length > 0 && (
                            <>
                                <p>
                                    {formatMessage(MESSAGES.errors, {
                                        count: notificationImport.errors.length,
                                    })}
                                </p>
                                <pre style={{ maxHeight: '550px' }}>
                                    {JSON.stringify(
                                        notificationImport.errors,
                                        null,
                                        ' ',
                                    )}
                                </pre>
                            </>
                        )}
                </>
            )}
        </AlertModal>
    );
};

type ButtonProps = {
    onClick: () => void;
    dataTestId?: string;
};

const NotificationImportDetailButton: FunctionComponent<ButtonProps> = ({
    onClick,
    dataTestId = 'open-polio-notifications-import-details-button',
}) => (
    <IconButton
        dataTestId={dataTestId}
        onClick={onClick}
        overrideIcon={VisibilityIcon}
        tooltipMessage={MESSAGES.details}
    />
);

const NotificationImportDetail = makeFullModal(
    NotificationImportDetailModal,
    NotificationImportDetailButton,
);

type Props = {
    task: Task<unknown>;
};

export const PolioNotificationTaskAction: FunctionComponent<Props> = ({
    task,
}) => {
    const currentUser = useCurrentUser();
    const canSeeImport = userHasPermission(NOTIFICATION, currentUser);
    if (
        !canSeeImport ||
        !['SUCCESS', 'ERRORED'].includes(task.status) ||
        task.name !== 'create_polio_notifications_async'
    ) {
        return null;
    }
    return <NotificationImportDetail task={task} iconProps={{}} />;
};

PolioNotificationTaskAction.displayName = 'PolioNotificationTaskAction';
